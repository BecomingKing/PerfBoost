"""垃圾清理引擎：直接删除，删不掉的提示用户."""

import os
import ctypes
import subprocess
from dataclasses import dataclass, field


# ---- 回收站操作 ----

def _empty_recycle_bin_shell() -> bool:
    """清空回收站。"""
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        return True
    except Exception:
        return False


def _get_recycle_bin_size_shell() -> int:
    """获取回收站大小。"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$s=(Get-ChildItem -Path 'C:\\$Recycle.Bin' -Recurse -Force "
             "-ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; "
             "if($s){$s}else{0}"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return int(result.stdout.strip() or 0)
    except Exception:
        return 0


# ---- 数据模型 ----

@dataclass
class CleanCategory:
    key: str
    label: str
    paths: list[str] = field(default_factory=list)
    total_size: int = 0
    files: list[tuple[str, int]] = field(default_factory=list)
    needs_admin: bool = False
    risk_level: str = "safe"          # "safe" | "caution" | "danger"
    explanation: str = ""             # 大白话解释


class JunkCleaner:
    """垃圾文件扫描与清理。"""

    MAX_PREVIEW_FILES = 500

    def __init__(self):
        self._categories: list[CleanCategory] = []
        self._last_skipped: list[str] = []

    # ========== 扫描 ==========

    def scan(self) -> list[CleanCategory]:
        self._categories = []

        # 1. 用户临时文件
        user_temp = os.environ.get("TEMP") or os.environ.get("TMP") or ""
        temp_cat = CleanCategory(
            key="temp", label="用户临时文件", needs_admin=False,
            risk_level="safe",
            explanation="软件运行时产生的临时文件，删了完全不影响使用",
        )
        if user_temp and os.path.isdir(user_temp):
            temp_cat.paths.append(user_temp)
        self._collect_files(temp_cat)
        self._categories.append(temp_cat)

        # 2. 浏览器缓存
        browser_paths = _get_browser_cache_paths()
        browser_cat = CleanCategory(
            key="browser_cache", label="浏览器缓存", needs_admin=False,
            paths=browser_paths,
            risk_level="safe",
            explanation="浏览器存的网页图片和文件，删了不影响密码和收藏，网页重新加载即可",
        )
        self._collect_files(browser_cat)
        self._categories.append(browser_cat)

        # 3. 回收站
        recycle_cat = CleanCategory(
            key="recycle_bin", label="回收站", needs_admin=False,
            risk_level="safe",
            explanation="你已经删过的文件，清空后释放它们占用的空间",
        )
        recycle_cat.total_size = _get_recycle_bin_size_shell()
        self._categories.append(recycle_cat)

        # 4. 错误报告
        crash_dirs = _get_crash_dump_dirs()
        crash_cat = CleanCategory(
            key="crash_dumps", label="错误报告 & 崩溃转储", needs_admin=False,
            paths=crash_dirs,
            risk_level="safe",
            explanation="软件崩溃时生成的调试文件，对普通用户没任何用处",
        )
        self._collect_files(crash_cat)
        self._categories.append(crash_cat)

        # 5. 系统临时文件
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        sys_temp = os.path.join(system_root, "Temp")
        sys_temp_cat = CleanCategory(
            key="system_temp", label="系统临时文件",
            paths=[sys_temp] if os.path.isdir(sys_temp) else [],
            needs_admin=True,
            risk_level="caution",
            explanation="Windows 自己的临时文件，一般安全但需要管理员权限",
        )
        self._collect_files(sys_temp_cat)
        self._categories.append(sys_temp_cat)

        # 6. Windows 日志
        log_dirs = [
            os.path.join(system_root, "Logs"),
            os.path.join(system_root, "System32", "winevt", "Logs"),
        ]
        log_cat = CleanCategory(
            key="windows_logs", label="Windows 日志文件",
            paths=[d for d in log_dirs if os.path.isdir(d)],
            needs_admin=True,
            risk_level="danger",
            explanation="系统运行记录，出问题时排查用，建议保留",
        )
        self._collect_files(log_cat)
        self._categories.append(log_cat)

        # 7. 缩略图缓存
        thumb_cat = CleanCategory(
            key="thumbnails", label="缩略图缓存", needs_admin=True,
            risk_level="caution",
            explanation="文件夹里图片视频的预览小图，删了下次打开文件夹会重新生成，略慢",
        )
        thumb_paths = _find_thumbcache_files(system_root)
        thumb_cat.paths = thumb_paths
        thumb_cat.total_size = sum(
            os.path.getsize(p) for p in thumb_paths if os.path.isfile(p)
        )
        for p in thumb_paths:
            if os.path.isfile(p):
                thumb_cat.files.append((p, os.path.getsize(p)))
        self._categories.append(thumb_cat)

        return self._categories

    # ========== 清理 ==========

    def clean(self, selected_keys: set[str]) -> tuple[int, list[str], list[str], list[str]]:
        """删除选中类别的文件。

        返回 (释放字节数, 已删列表, 无法删除列表, 重启后删列表)
        """
        freed = 0
        deleted: list[str] = []
        failed: list[str] = []
        pending: list[str] = []

        for cat in self._categories:
            if cat.key not in selected_keys:
                continue

            if cat.key == "recycle_bin":
                if _empty_recycle_bin_shell():
                    freed += cat.total_size
                    deleted.append(f"回收站 ({_format_size(cat.total_size)})")
                else:
                    failed.append("回收站清空失败")
                continue

            for path in cat.paths:
                if not os.path.exists(path):
                    continue
                if not _is_safe_path(path):
                    failed.append(f"{path} — 系统保护目录，已跳过")
                    continue

                f, d, fa, pe = _clean_path(path)
                freed += f
                deleted.extend(d)
                failed.extend(fa)
                pending.extend(pe)

        self._last_skipped = failed
        return freed, deleted, failed, pending

    @property
    def last_skipped(self) -> list[str]:
        return self._last_skipped

    # ========== 内部 ==========

    def _collect_files(self, cat: CleanCategory) -> None:
        total = 0
        for dir_path in cat.paths:
            if not os.path.isdir(dir_path):
                continue
            try:
                for entry in os.scandir(dir_path):
                    if len(cat.files) >= self.MAX_PREVIEW_FILES:
                        break
                    try:
                        if entry.is_file(follow_symlinks=False):
                            size = entry.stat().st_size
                            cat.files.append((entry.path, size))
                            total += size
                        elif entry.is_dir(follow_symlinks=False):
                            dir_size = _get_directory_size(entry.path)
                            cat.files.append((entry.path, dir_size))
                            total += dir_size
                    except (PermissionError, OSError):
                        continue
            except PermissionError:
                continue
        cat.total_size = total


# ---- 核心删除逻辑 ----

_MOVEFILE_REPLACE_EXISTING = 0x1
_MOVEFILE_DELAY_UNTIL_REBOOT = 0x4


def _force_delete_file(path: str) -> tuple[bool, bool]:
    """删除单个文件。先直接删，失败则标记重启后删。

    返回: (已释放, 需重启)
    """
    # 1. 直接删除
    try:
        os.unlink(path)
        return True, False
    except PermissionError:
        pass
    except OSError:
        pass

    # 2. 标记重启后删除
    try:
        ok = ctypes.windll.kernel32.MoveFileExW(
            path, None, _MOVEFILE_REPLACE_EXISTING | _MOVEFILE_DELAY_UNTIL_REBOOT,
        )
        if ok:
            return False, True
    except Exception:
        pass

    return False, False


def _clean_path(path: str) -> tuple[int, list[str], list[str], list[str]]:
    """删除一个文件或目录。

    返回: (释放字节, 已删列表, 失败列表, 重启后删列表)
    """
    freed = 0
    deleted: list[str] = []
    failed: list[str] = []
    pending: list[str] = []

    if os.path.isfile(path):
        size = os.path.getsize(path)
        released, needs_reboot = _force_delete_file(path)
        if released:
            freed += size
            deleted.append(path)
        elif needs_reboot:
            freed += size
            pending.append(path)
        else:
            failed.append(f"{path} — 文件被占用且无法标记删除")

    elif os.path.isdir(path):
        try:
            for entry in os.scandir(path):
                f, d, fa, pe = _clean_path(entry.path)
                freed += f
                deleted.extend(d)
                failed.extend(fa)
                pending.extend(pe)
            try:
                os.rmdir(path)
            except OSError:
                pass
        except PermissionError:
            failed.append(f"{path} — 目录无法访问")

    return freed, deleted, failed, pending


# ---- 扫描辅助 ----

def _get_browser_cache_paths() -> list[str]:
    local = os.environ.get("LOCALAPPDATA", "")
    roaming = os.environ.get("APPDATA", "")
    paths = []
    chrome = os.path.join(local, r"Google\Chrome\User Data\Default\Cache\Cache_Data")
    if os.path.isdir(chrome):
        paths.append(chrome)
    edge = os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache\Cache_Data")
    if os.path.isdir(edge):
        paths.append(edge)
    ff_profiles = os.path.join(roaming, r"Mozilla\Firefox\Profiles")
    if os.path.isdir(ff_profiles):
        for profile in os.listdir(ff_profiles):
            cache = os.path.join(ff_profiles, profile, "cache2")
            if os.path.isdir(cache):
                paths.append(cache)
    return paths


def _get_crash_dump_dirs() -> list[str]:
    local = os.environ.get("LOCALAPPDATA", "")
    paths = []
    crash_dumps = os.path.join(local, "CrashDumps")
    if os.path.isdir(crash_dumps):
        paths.append(crash_dumps)
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    minidump = os.path.join(system_root, "Minidump")
    if os.path.isdir(minidump):
        paths.append(minidump)
    return paths


def _find_thumbcache_files(system_root: str) -> list[str]:
    explorer_dir = os.path.join(system_root, "Explorer")
    if not os.path.isdir(explorer_dir):
        return []
    paths = []
    try:
        for entry in os.scandir(explorer_dir):
            if entry.is_file() and entry.name.lower().startswith("thumbcache_"):
                paths.append(entry.path)
    except PermissionError:
        pass
    return paths


def _get_directory_size(path: str) -> int:
    total = 0
    if not os.path.isdir(path):
        return 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += _get_directory_size(entry.path)
            except (PermissionError, OSError):
                continue
    except PermissionError:
        pass
    return total


def _is_safe_path(path: str) -> bool:
    path_lower = os.path.abspath(path).lower()
    system_root = os.environ.get("SystemRoot", r"C:\Windows").lower()
    protected = [
        os.path.join(system_root, "System32"),
        os.path.join(system_root, "SysWOW64"),
        os.path.join(system_root, "System"),
        os.path.join(system_root, "WinSxS"),
        os.path.join(system_root, "Boot"),
        os.path.join(system_root, "resources"),
        r"C:\Program Files",
        r"C:\Program Files (x86)",
    ]
    return not any(path_lower.startswith(p.lower()) for p in protected)


def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
