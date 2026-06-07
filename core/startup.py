"""启动项管理模块，读写注册表和启动文件夹."""

import json
import os
import winreg
from dataclasses import dataclass, asdict

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
BACKUP_DIR = os.path.join(CONFIG_DIR, "backup")
BACKUP_PATH = os.path.join(BACKUP_DIR, "startup_backup.json")


@dataclass
class StartupEntry:
    name: str
    command: str
    source: str          # "HKCU", "HKLM", "StartupFolder"
    enabled: bool = True


class StartupManager:
    """启动项管理器."""

    RUN_KEYS = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
    ]

    def get_entries(self) -> list[StartupEntry]:
        """获取所有启动项."""
        entries: list[StartupEntry] = []

        for hkey, subkey, source in self.RUN_KEYS:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            entries.append(StartupEntry(
                                name=name,
                                command=value,
                                source=source,
                            ))
                            i += 1
                        except OSError:
                            break
            except OSError:
                pass

        for folder_label, folder_path in [
            ("StartupFolder (用户)", os.path.join(
                os.environ.get("APPDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )),
            ("StartupFolder (公共)", os.path.join(
                os.environ.get("ALLUSERSPROFILE", ""),
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )),
        ]:
            if os.path.isdir(folder_path):
                for fname in os.listdir(folder_path):
                    full = os.path.join(folder_path, fname)
                    if fname.endswith(".lnk") or os.path.isfile(full):
                        entries.append(StartupEntry(
                            name=fname.replace(".lnk", ""),
                            command=full,
                            source=folder_label,
                        ))

        return entries

    def disable_entry(self, entry: StartupEntry) -> bool:
        """禁用启动项，执行前先备份到文件."""
        self._backup_entry(entry)

        if entry.source in ("HKCU", "HKLM"):
            hkey = winreg.HKEY_CURRENT_USER if entry.source == "HKCU" else winreg.HKEY_LOCAL_MACHINE
            try:
                with winreg.OpenKey(
                    hkey,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE,
                ) as key:
                    winreg.DeleteValue(key, entry.name)
                return True
            except OSError:
                return False
        elif "StartupFolder" in entry.source:
            try:
                os.unlink(entry.command)
                return True
            except OSError:
                return False
        return False

    def enable_entry(self, entry: StartupEntry) -> bool:
        """重新启用启动项（恢复写入注册表）."""
        if entry.source in ("HKCU", "HKLM"):
            hkey = winreg.HKEY_CURRENT_USER if entry.source == "HKCU" else winreg.HKEY_LOCAL_MACHINE
            try:
                with winreg.OpenKey(
                    hkey,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE,
                ) as key:
                    winreg.SetValueEx(key, entry.name, 0, winreg.REG_SZ, entry.command)
                return True
            except OSError:
                return False
        return False

    # ---- 备份与恢复 ----

    def _backup_entry(self, entry: StartupEntry) -> None:
        """将启动项备份到文件."""
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backups = self._load_backups()
        # 避免重复备份
        for b in backups:
            if b["name"] == entry.name and b["source"] == entry.source:
                return
        backups.append(asdict(entry))
        with open(BACKUP_PATH, "w", encoding="utf-8") as f:
            json.dump(backups, f, indent=2, ensure_ascii=False)

    def get_backups(self) -> list[StartupEntry]:
        """获取所有已备份的启动项."""
        raw = self._load_backups()
        return [StartupEntry(**item) for item in raw]

    def restore_entry(self, entry: StartupEntry) -> bool:
        """恢复一个启动项到注册表或启动文件夹，并从备份中移除."""
        success = self.enable_entry(entry)
        if success:
            self._remove_backup(entry)
        return success

    def _load_backups(self) -> list[dict]:
        if not os.path.isfile(BACKUP_PATH):
            return []
        try:
            with open(BACKUP_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _remove_backup(self, entry: StartupEntry) -> None:
        backups = self._load_backups()
        backups = [b for b in backups
                   if not (b["name"] == entry.name and b["source"] == entry.source)]
        with open(BACKUP_PATH, "w", encoding="utf-8") as f:
            json.dump(backups, f, indent=2, ensure_ascii=False)

    # ---- 影响评估 ----

    @staticmethod
    def _extract_exe_path(command: str):  # -> str | None  (Python 3.10+ syntax)
        """从启动命令中提取可执行文件的实际路径.

        处理三种格式:
        1. "C:\\Program Files\\Foo\\bar.exe" /arg  — 引号包裹
        2. C:\\Foo\\bar.exe /arg                     — 无引号无空格
        3. C:\\Program Files\\Foo\\bar.exe /arg      — 无引号有空格
        同时展开 %ProgramFiles% 等环境变量.
        """
        expanded = os.path.expandvars(command)

        # 情况1: 引号包裹的路径
        if expanded.startswith('"'):
            end = expanded.find('"', 1)
            if end > 0:
                return expanded[1:end]

        # 情况2/3: 无引号，从右向左逐步拼接找存在的文件
        parts = expanded.split()
        for i in range(len(parts), 0, -1):
            candidate = " ".join(parts[:i])
            if os.path.isfile(candidate):
                return candidate

        # 兜底：至少返回第一个 token 用于错误提示
        return parts[0] if parts else None

    @staticmethod
    def _resolve_lnk_target(lnk_path: str):  # -> str | None  (Python 3.10+ syntax)
        """解析 .lnk 快捷方式指向的实际目标路径."""
        try:
            import subprocess
            ps_cmd = (
                f'(New-Object -ComObject WScript.Shell)'
                f'.CreateShortcut("{lnk_path}").TargetPath'
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=5,
            )
            target = result.stdout.strip()
            return target if target else None
        except Exception:
            return None

    def get_impact_estimate(self, entry: StartupEntry) -> str:
        """评估禁用此启动项的影响."""
        # 启动文件夹的快捷方式 — 解析 .lnk 指向的真实目标
        if entry.command.lower().endswith(".lnk"):
            target = self._resolve_lnk_target(entry.command)
            if target and os.path.exists(target):
                return "快捷方式｜目标存在，禁用后不再自启"
            elif target:
                return "快捷方式｜目标已卸载，可安全禁用"
            return "快捷方式｜无法解析，可安全禁用"

        # 注册表启动项 — 提取 exe 路径并检查是否存在
        exe_path = self._extract_exe_path(entry.command)
        if exe_path and os.path.exists(exe_path):
            return "程序文件存在｜禁用后该程序不再自启"
        elif exe_path:
            return "文件不存在｜可能已卸载，可安全禁用"
        return "注册表项｜禁用后不再自启"

    @staticmethod
    def get_boot_delay_estimate(entry) -> str:
        """估算启动项对开机时间的拖慢程度，返回一句人话。

        根据程序 exe 文件大小粗略估算。不追求精确计时，
        目的是给用户一个"关掉的理由"。
        """
        # 启动文件夹快捷方式 — 解析 .lnk 指向的真实目标
        if entry.command.lower().endswith(".lnk"):
            target = StartupManager._resolve_lnk_target(entry.command)
            if not target or not os.path.exists(target):
                return "该程序已卸载，可安全禁用"
            exe_path = target
        else:
            exe_path = StartupManager._extract_exe_path(entry.command)

        if not exe_path or not os.path.exists(exe_path):
            return "该程序已卸载，可安全禁用"

        # 获取 exe 大小（MB）
        try:
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        except OSError:
            return "无法评估｜可手动禁用"

        # 粗略估算：每 MB 约 0.03 秒，最低 0.3 秒，最高 15 秒
        delay = max(0.3, min(15.0, size_mb * 0.03))
        return f"⏱ 预估拖慢开机 {delay:.1f} 秒"

    def is_dead_entry(self, entry: StartupEntry) -> bool:
        """判断启动项是否指向已不存在的文件（软件已卸载）."""
        if entry.command.lower().endswith(".lnk"):
            target = self._resolve_lnk_target(entry.command)
            return target is None or not os.path.exists(target)

        exe_path = self._extract_exe_path(entry.command)
        return exe_path is not None and not os.path.exists(exe_path)
