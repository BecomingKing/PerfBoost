# PerfBoost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

---

## 📋 计划概览

**目标：** 构建 Windows 桌面系统性能优化工具，包含硬件监控仪表盘、垃圾清理、启动项管理、进程管理四大模块。

**技术栈：** Python 3.11+ / CustomTkinter (GUI) / psutil (系统信息) / winreg (注册表) / PyInstaller (打包)

**架构：** 单体多线程，三层分离：
- `ui/` — CustomTkinter 页面，纯展示 + 事件绑定
- `core/` — 核心逻辑，不依赖 UI（psutil 采样、垃圾扫描、注册表读写、进程管理）
- `utils/` — 通用工具（字节格式化、权限检查、JSON 配置单例）

**数据流：** `后台监控线程 → queue.Queue → UI 定时器轮询 → 组件更新`

### Task 依赖关系

```
Task 1 (脚手架)
  ├─→ Task 2 (utils/helpers)
  ├─→ Task 3 (utils/config)
  │     ├─→ Task 4 (core/monitor)
  │     ├─→ Task 5 (core/cleaner)
  │     ├─→ Task 6 (core/startup)
  │     └─→ Task 7 (core/process)
  │           ├─→ Task 8 (ui/dashboard)   ← 依赖 Task 3+4
  │           ├─→ Task 9 (ui/cleaner)     ← 依赖 Task 3+5
  │           ├─→ Task 10 (ui/startup)    ← 依赖 Task 3+6
  │           └─→ Task 11 (ui/process)    ← 依赖 Task 7
  │                 └─→ Task 12 (app.py + main.py 串联)
  │                       └─→ Task 13 (.gitignore + README)
```

### Task 清单

| # | Task | 产出文件 | 说明 |
|---|------|---------|------|
| 1 | 项目脚手架 | `requirements.txt`, `__init__.py`×3, `.gitkeep` | git init + pip install |
| 2 | Utils — Helpers | `utils/helpers.py` | format_bytes, is_admin, 临时目录, 浏览器缓存路径, 安全路径检查 |
| 3 | Utils — Config | `utils/config.py` | JSON 配置单例，读写 `%APPDATA%/PerfBoost/config.json` |
| 4 | Core — Monitor | `core/monitor.py` | 后台线程 psutil 采样，queue 推送 CPU/内存/磁盘/温度/网速 |
| 5 | Core — Cleaner | `core/cleaner.py` | 垃圾扫描 + 分类 + 清理引擎，支持 5 类清理 + 安全约束 |
| 6 | Core — Startup | `core/startup.py` | 注册表 Run 键 + 启动文件夹读写，启用/禁用 |
| 7 | Core — Process | `core/process.py` | psutil 进程列表 + 终止 + 系统关键进程保护 |
| 8 | UI — Dashboard | `ui/dashboard.py` | 仪表盘 Tab：进度条 + 磁盘列表 + 温度 + 网速 |
| 9 | UI — Cleaner | `ui/cleaner.py` | 清理 Tab：扫描按钮 + 分类勾选 + 清理进度 |
| 10 | UI — Startup | `ui/startup.py` | 启动项 Tab：列表 + 启用/禁用开关 |
| 11 | UI — Process | `ui/process.py` | 进程 Tab：搜索 + 列表 + PID 终止 |
| 12 | App Shell | `app.py`, `main.py` | CustomTkinter 主窗口 + TabView 容器串联 |
| 13 | 收尾 | `.gitignore`, `README.md` | 忽略规则 + 使用说明 |

**总文件数：** 14 个源文件 + 2 个配置文件

**预估工作量：** 每个 Task 10-15 分钟（含 git commit），总计约 2.5-3 小时。

**执行策略：** 严格按顺序执行（上游 Task 完成后下游才能跑）。Task 1-7 无 GUI 依赖可快速推进；Task 8-12 为 UI 层需逐个验证。

---

**Goal:** Build a Windows system optimization tool with hardware monitor dashboard, junk cleaner, startup manager, and process manager using Python + CustomTkinter.

**Architecture:** Single-process multi-threaded app. Layer: UI (CustomTkinter frames) → Core (psutil/winreg logic) → Utils (config, helpers). Background thread samples system metrics via `queue.Queue`; UI timer consumes and renders.

**Tech Stack:** Python 3.11+, CustomTkinter, psutil, PyInstaller

---

## File Map

```
perfboost/
├── main.py                 # Entry point
├── app.py                  # Main window + TabView + thread orchestration
├── requirements.txt        # Dependencies
├── ui/
│   ├── __init__.py
│   ├── dashboard.py        # Dashboard tab frame
│   ├── cleaner.py          # Cleaner tab frame
│   ├── startup.py          # Startup tab frame
│   └── process.py          # Process tab frame
├── core/
│   ├── __init__.py
│   ├── monitor.py          # System metrics sampling
│   ├── cleaner.py          # Junk scan & clean engine
│   ├── startup.py          # Startup entry read/write
│   └── process.py          # Process enumeration & kill
├── utils/
│   ├── __init__.py
│   ├── config.py           # JSON config read/write
│   └── helpers.py          # format_bytes, is_admin, etc.
└── assets/                 # Icons (placeholder for now)
```

---

### Task 1: Project Scaffolding

**Files:** Create `requirements.txt`, `utils/__init__.py`, `core/__init__.py`, `ui/__init__.py`, `assets/.gitkeep`

- [ ] **Step 1: Initialize git repo**

```bash
cd E:/Projects/perfboost && git init
```

- [ ] **Step 2: Create requirements.txt**

Write `requirements.txt`:
```
customtkinter>=5.2.0
psutil>=5.9.0
```

- [ ] **Step 3: Create package init files and assets placeholder**

```bash
mkdir -p E:/Projects/perfboost/utils E:/Projects/perfboost/core E:/Projects/perfboost/ui E:/Projects/perfboost/assets
touch E:/Projects/perfboost/utils/__init__.py
touch E:/Projects/perfboost/core/__init__.py
touch E:/Projects/perfboost/ui/__init__.py
touch E:/Projects/perfboost/assets/.gitkeep
```

- [ ] **Step 4: Install dependencies**

```bash
cd E:/Projects/perfboost && pip install -r requirements.txt
```

- [ ] **Step 5: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "chore: project scaffolding with dependencies"
```

---

### Task 2: Utils — Helpers

**Files:** Create `utils/helpers.py`

- [ ] **Step 1: Write helpers.py**

```python
"""通用工具函数."""

import os
import ctypes


def format_bytes(size: int) -> str:
    """将字节数格式化为人类可读的字符串."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def is_admin() -> bool:
    """检查当前进程是否以管理员权限运行."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_temp_dirs() -> list[str]:
    """返回常见的临时文件目录列表."""
    dirs = []
    # 用户临时目录
    user_temp = os.environ.get("TEMP") or os.environ.get("TMP")
    if user_temp and os.path.isdir(user_temp):
        dirs.append(user_temp)
    # 系统临时目录
    system_temp = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp")
    if os.path.isdir(system_temp):
        dirs.append(system_temp)
    return dirs


def get_browser_cache_dirs() -> list[tuple[str, str]]:
    """返回浏览器缓存目录列表，每项为 (浏览器名, 缓存路径)."""
    local = os.environ.get("LOCALAPPDATA", "")
    browsers = []
    # Chrome
    chrome = os.path.join(local, r"Google\Chrome\User Data\Default\Cache\Cache_Data")
    if os.path.isdir(chrome):
        browsers.append(("Chrome", chrome))
    # Edge
    edge = os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache\Cache_Data")
    if os.path.isdir(edge):
        browsers.append(("Edge", edge))
    # Firefox
    roaming = os.environ.get("APPDATA", "")
    firefox_profiles = os.path.join(roaming, r"Mozilla\Firefox\Profiles")
    if os.path.isdir(firefox_profiles):
        for profile in os.listdir(firefox_profiles):
            cache = os.path.join(firefox_profiles, profile, "cache2")
            if os.path.isdir(cache):
                browsers.append(("Firefox", cache))
    return browsers


def get_directory_size(path: str) -> int:
    """递归计算目录总大小（字节），不存在的目录返回0."""
    total = 0
    if not os.path.isdir(path):
        return 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_directory_size(entry.path)
            except (PermissionError, OSError):
                continue
    except PermissionError:
        pass
    return total


def is_safe_path(path: str) -> bool:
    """检查路径是否安全可清理（不在系统保护目录内）."""
    path_lower = os.path.abspath(path).lower()
    system_root = os.environ.get("SystemRoot", r"C:\Windows").lower()

    # 不碰这些关键目录
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
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add helpers utility module"
```

---

### Task 3: Utils — Config

**Files:** Create `utils/config.py`

- [ ] **Step 1: Write config.py**

```python
"""配置持久化模块，读写 %APPDATA%/PerfBoost/config.json."""

import json
import os
from typing import Any

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", ""), "PerfBoost")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG: dict[str, Any] = {
    "clean_categories": {
        "temp": True,
        "browser_cache": True,
        "recycle_bin": True,
        "windows_logs": False,
        "thumbnails": False,
    },
    "monitor_interval": 1,
    "temperature_unit": "celsius",
    "startup_disabled": [],
    "last_optimization": None,
    "total_cleaned_bytes": 0,
}


class Config:
    """单例配置管理器."""

    _instance = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = DEFAULT_CONFIG.copy()
            cls._instance._loaded = False
        return cls._instance

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # 合并缺失的默认键
                for key, value in DEFAULT_CONFIG.items():
                    if key not in loaded:
                        loaded[key] = value
                self._data = loaded
            except (json.JSONDecodeError, IOError):
                pass
        self._loaded = True

    def get(self, key: str, default: Any = None) -> Any:
        self._ensure_loaded()
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._ensure_loaded()
        self._data[key] = value
        self._save()

    def _save(self) -> None:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def save(self) -> None:
        """强制保存当前状态到文件."""
        self._save()
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add config persistence module"
```

---

### Task 4: Core — Monitor

**Files:** Create `core/monitor.py`

- [ ] **Step 1: Write monitor.py**

```python
"""系统硬件监控模块，封装 psutil 采样逻辑."""

import time
import threading
import queue

import psutil


class SystemMonitor:
    """后台线程持续采样系统指标，通过队列推送给UI."""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False
        # 网络速率计算需要记录上一次采样
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = time.time()

    @property
    def data_queue(self) -> queue.Queue:
        return self._queue

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while self._running:
            try:
                snapshot = self._sample()
                self._queue.put(snapshot)
            except Exception:
                self._queue.put({"error": "采样失败"})
            time.sleep(self.interval)

    def _sample(self) -> dict:
        now = time.time()

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0)

        # 内存
        mem = psutil.virtual_memory()

        # 磁盘
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                # 只显示固定磁盘
                if "fixed" in part.opts.lower() or part.fstype:
                    disks.append({
                        "mountpoint": part.mountpoint,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    })
            except PermissionError:
                continue

        # 温度
        temperature = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        temperature = entries[0].current
                        break
        except Exception:
            pass

        # 网络速率
        net_io = psutil.net_io_counters()
        elapsed = now - self._last_net_time
        upload = (net_io.bytes_sent - self._last_net_io.bytes_sent) / max(elapsed, 0.001)
        download = (net_io.bytes_recv - self._last_net_io.bytes_recv) / max(elapsed, 0.001)
        self._last_net_io = net_io
        self._last_net_time = now

        return {
            "cpu_percent": cpu_percent,
            "memory_total": mem.total,
            "memory_used": mem.used,
            "memory_percent": mem.percent,
            "disks": disks,
            "temperature": temperature,
            "net_upload": upload,
            "net_download": download,
        }
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add system monitor core module"
```

---

### Task 5: Core — Cleaner

**Files:** Create `core/cleaner.py`

- [ ] **Step 1: Write cleaner.py**

```python
"""垃圾清理引擎：扫描临时文件、浏览器缓存、回收站、日志等."""

import os
import shutil
import subprocess
from dataclasses import dataclass, field

from utils.helpers import (
    get_temp_dirs,
    get_browser_cache_dirs,
    get_directory_size,
    is_safe_path,
)


@dataclass
class CleanCategory:
    key: str
    label: str
    paths: list[str] = field(default_factory=list)
    total_size: int = 0


class JunkCleaner:
    """垃圾文件扫描与清理."""

    def __init__(self):
        self._categories: list[CleanCategory] = []

    def scan(self) -> list[CleanCategory]:
        """扫描所有可清理类别，返回带大小信息的列表."""
        self._categories = []

        # 1. 临时文件
        temp_cat = CleanCategory(key="temp", label="系统临时文件")
        for d in get_temp_dirs():
            temp_cat.paths.append(d)
        temp_cat.total_size = sum(get_directory_size(p) for p in temp_cat.paths)
        self._categories.append(temp_cat)

        # 2. 浏览器缓存
        browsers = get_browser_cache_dirs()
        browser_paths = [p for _, p in browsers]
        browser_cat = CleanCategory(
            key="browser_cache",
            label="浏览器缓存",
            paths=browser_paths,
        )
        browser_cat.total_size = sum(get_directory_size(p) for p in browser_paths)
        self._categories.append(browser_cat)

        # 3. 回收站
        recycle_cat = CleanCategory(key="recycle_bin", label="回收站")
        recycle_cat.total_size = self._get_recycle_bin_size()
        self._categories.append(recycle_cat)

        # 4. Windows 日志
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        log_dirs = [
            os.path.join(system_root, "Logs"),
            os.path.join(system_root, "System32", "winevt", "Logs"),
        ]
        log_cat = CleanCategory(
            key="windows_logs",
            label="Windows 日志文件",
            paths=[d for d in log_dirs if os.path.isdir(d)],
        )
        log_cat.total_size = sum(get_directory_size(p) for p in log_cat.paths)
        self._categories.append(log_cat)

        # 5. 缩略图缓存
        thumb_paths = []
        for root, dirs, files in os.walk(
            os.path.join(system_root, "Explorer"), topdown=True
        ):
            for f in files:
                if f.startswith("thumbcache_"):
                    fp = os.path.join(root, f)
                    thumb_paths.append(fp)
            break  # 只扫描顶层
        thumb_cat = CleanCategory(
            key="thumbnails",
            label="缩略图缓存",
            paths=thumb_paths,
        )
        thumb_cat.total_size = sum(
            os.path.getsize(p) for p in thumb_paths if os.path.isfile(p)
        )
        self._categories.append(thumb_cat)

        return self._categories

    def clean(self, selected_keys: set[str]) -> tuple[int, list[str]]:
        """清理选中的类别，返回 (释放字节数, 错误列表)."""
        freed = 0
        errors: list[str] = []

        for cat in self._categories:
            if cat.key not in selected_keys:
                continue

            if cat.key == "recycle_bin":
                f, err = self._empty_recycle_bin()
                freed += f
                errors.extend(err)
                continue

            for path in cat.paths:
                if not os.path.exists(path) or not is_safe_path(path):
                    continue
                try:
                    size_before = get_directory_size(path)
                    if os.path.isfile(path):
                        os.unlink(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    freed += size_before
                except (PermissionError, OSError) as e:
                    errors.append(f"{path}: {e}")

        return freed, errors

    def _get_recycle_bin_size(self) -> int:
        """获取回收站大致大小."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-ChildItem -Path 'C:\\$Recycle.Bin' -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum"],
                capture_output=True, text=True, timeout=10,
            )
            return int(result.stdout.strip() or 0)
        except Exception:
            return 0

    def _empty_recycle_bin(self) -> tuple[int, list[str]]:
        """清空回收站."""
        try:
            subprocess.run(
                ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction Stop"],
                capture_output=True, text=True, timeout=30,
            )
            return 0, []
        except Exception as e:
            return 0, [f"清空回收站失败: {e}"]
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add junk cleaner core module"
```

---

### Task 6: Core — Startup Manager

**Files:** Create `core/startup.py`

- [ ] **Step 1: Write startup.py**

```python
"""启动项管理模块，读写注册表和启动文件夹."""

import os
import winreg
from dataclasses import dataclass


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

        # 注册表 Run 键
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

        # 启动文件夹
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
        """禁用启动项（将其从注册表/启动文件夹移除，备份到配置）."""
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
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add startup manager core module"
```

---

### Task 7: Core — Process Manager

**Files:** Create `core/process.py`

- [ ] **Step 1: Write process.py**

```python
"""进程管理模块."""

import psutil


class ProcessManager:
    """进程管理器，提供进程列表和结束进程功能."""

    # 不可终止的关键系统进程
    PROTECTED_NAMES = {"System", "System Idle Process", "svchost.exe", "csrss.exe",
                       "wininit.exe", "winlogon.exe", "services.exe", "lsass.exe",
                       "smss.exe", "audiodg.exe"}

    def get_processes(self) -> list[dict]:
        """获取所有进程列表，按内存降序排列."""
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                info = proc.info
                mem_mb = info["memory_info"].rss / (1024 * 1024) if info["memory_info"] else 0
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "cpu_percent": info["cpu_percent"] or 0,
                    "memory_mb": round(mem_mb, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda p: p["memory_mb"], reverse=True)
        return procs

    def kill_process(self, pid: int) -> bool:
        """终止指定进程，返回是否成功."""
        try:
            proc = psutil.Process(pid)
            if proc.name() in self.PROTECTED_NAMES:
                return False
            proc.terminate()
            proc.wait(timeout=3)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            return False

    def is_protected(self, pid: int) -> bool:
        """检查是否为受保护的系统进程."""
        try:
            proc = psutil.Process(pid)
            return proc.name() in self.PROTECTED_NAMES
        except psutil.NoSuchProcess:
            return False
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add process manager core module"
```

---

### Task 8: UI — Dashboard Tab

**Files:** Create `ui/dashboard.py`

- [ ] **Step 1: Write dashboard.py**

```python
"""仪表盘 Tab：CPU、内存、磁盘、温度、网速实时显示."""

import customtkinter as ctk
import queue

from utils.helpers import format_bytes


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, monitor, config, **kwargs):
        super().__init__(master, **kwargs)
        self.monitor = monitor
        self.config = config
        self._build_ui()
        self._start_polling()

    def _build_ui(self):
        # 上两列：CPU + 内存
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))

        left = ctk.CTkFrame(top)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(left, text="CPU 使用率", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        self.cpu_bar = ctk.CTkProgressBar(left, width=200)
        self.cpu_bar.pack(pady=10)
        self.cpu_bar.set(0)
        self.cpu_label = ctk.CTkLabel(left, text="0%", font=ctk.CTkFont(size=28, weight="bold"))
        self.cpu_label.pack(pady=(0, 10))

        right = ctk.CTkFrame(top)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(right, text="内存 使用率", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        self.mem_bar = ctk.CTkProgressBar(right, width=200)
        self.mem_bar.pack(pady=10)
        self.mem_bar.set(0)
        self.mem_label = ctk.CTkLabel(right, text="0%", font=ctk.CTkFont(size=28, weight="bold"))
        self.mem_label.pack(pady=2)
        self.mem_detail = ctk.CTkLabel(right, text="0 / 0 GB", font=ctk.CTkFont(size=12))
        self.mem_detail.pack(pady=(0, 10))

        # 磁盘区域
        disk_frame = ctk.CTkFrame(self)
        disk_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(disk_frame, text="磁盘使用", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(10, 5))
        self.disk_container = ctk.CTkFrame(disk_frame, fg_color="transparent")
        self.disk_container.pack(fill="x", padx=10, pady=(0, 10))
        self.disk_widgets: list[tuple[ctk.CTkLabel, ctk.CTkProgressBar, ctk.CTkLabel]] = []

        # 底部：温度 + 网速
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=10)

        temp_frame = ctk.CTkFrame(bottom)
        temp_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(temp_frame, text="CPU 温度", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        self.temp_label = ctk.CTkLabel(temp_frame, text="-- °C", font=ctk.CTkFont(size=28, weight="bold"))
        self.temp_label.pack(pady=10)

        net_frame = ctk.CTkFrame(bottom)
        net_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(net_frame, text="网络速率", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        self.net_label = ctk.CTkLabel(net_frame, text="↑ 0 B/s\n↓ 0 B/s",
                                      font=ctk.CTkFont(size=16))
        self.net_label.pack(pady=10)

        # 统计摘要
        summary = ctk.CTkFrame(self)
        summary.pack(fill="x", padx=20, pady=(10, 20))
        last_opt = self.config.get("last_optimization")
        last_text = f"上次优化: {last_opt}" if last_opt else "尚未优化"
        ctk.CTkLabel(summary, text=last_text, font=ctk.CTkFont(size=11)).pack(side="left", padx=10, pady=5)
        cleaned = self.config.get("total_cleaned_bytes", 0)
        ctk.CTkLabel(summary, text=f"已清理: {format_bytes(cleaned)}",
                     font=ctk.CTkFont(size=11)).pack(side="right", padx=10, pady=5)

    def _start_polling(self):
        """开启定时轮询，从队列取数据更新UI."""
        self._poll()

    def _poll(self):
        try:
            while True:
                data = self.monitor.data_queue.get_nowait()
                if "error" in data:
                    continue
                self._update(data)
        except queue.Empty:
            pass
        self.after(1000, self._poll)

    def _update(self, data: dict):
        cpu = data["cpu_percent"]
        self.cpu_bar.set(cpu / 100)
        self.cpu_label.configure(text=f"{cpu:.0f}%")

        mem_pct = data["memory_percent"]
        self.mem_bar.set(mem_pct / 100)
        self.mem_label.configure(text=f"{mem_pct:.0f}%")
        used_str = format_bytes(data["memory_used"])
        total_str = format_bytes(data["memory_total"])
        self.mem_detail.configure(text=f"{used_str} / {total_str}")

        self._update_disks(data.get("disks", []))
        self._update_temperature(data.get("temperature"))
        self._update_network(data.get("net_upload", 0), data.get("net_download", 0))

    def _update_disks(self, disks: list[dict]):
        # 清除旧 widgets
        for label, bar, detail in self.disk_widgets:
            label.destroy()
            bar.destroy()
            detail.destroy()
        self.disk_widgets.clear()

        for disk in disks:
            row = ctk.CTkFrame(self.disk_container, fg_color="transparent")
            row.pack(fill="x", pady=2)
            label = ctk.CTkLabel(row, text=f"{disk['mountpoint']} ", width=40)
            label.pack(side="left")
            bar = ctk.CTkProgressBar(row, width=300)
            bar.pack(side="left", padx=5)
            bar.set(disk["percent"] / 100)
            used = format_bytes(disk["used"])
            total = format_bytes(disk["total"])
            detail = ctk.CTkLabel(row, text=f"{used} / {total}")
            detail.pack(side="left", padx=5)
            self.disk_widgets.append((label, bar, detail))

    def _update_temperature(self, temp):
        if temp is not None:
            self.temp_label.configure(text=f"{temp:.0f}°C")
        else:
            self.temp_label.configure(text="N/A")

    def _update_network(self, upload, download):
        self.net_label.configure(
            text=f"↑ {format_bytes(int(upload))}/s\n↓ {format_bytes(int(download))}/s"
        )
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add dashboard UI tab"
```

---

### Task 9: UI — Cleaner Tab

**Files:** Create `ui/cleaner.py`

- [ ] **Step 1: Write cleaner.py**

```python
"""清理 Tab：垃圾扫描 + 一键清理."""

import customtkinter as ctk
from datetime import datetime

from core.cleaner import JunkCleaner
from utils.helpers import format_bytes
from utils.config import Config


class CleanerFrame(ctk.CTkFrame):
    def __init__(self, master, config: Config, **kwargs):
        super().__init__(master, **kwargs)
        self.config = config
        self.cleaner = JunkCleaner()
        self._categories = []
        self._checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self._size_labels: dict[str, ctk.CTkLabel] = {}
        self._build_ui()

    def _build_ui(self):
        # 标题
        ctk.CTkLabel(self, text="垃圾清理", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))

        # 扫描按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        self.scan_btn = ctk.CTkButton(btn_frame, text="🔍 扫描垃圾文件", command=self._on_scan)
        self.scan_btn.pack(side="left", padx=5)
        self.clean_btn = ctk.CTkButton(btn_frame, text="🧹 一键清理", command=self._on_clean,
                                       state="disabled", fg_color="#c0392b", hover_color="#e74c3c")
        self.clean_btn.pack(side="left", padx=5)

        # 进度条
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=5)
        self.progress.set(0)
        self.status_label = ctk.CTkLabel(self, text="就绪", font=ctk.CTkFont(size=11))
        self.status_label.pack()

        # 分类列表容器
        self.cat_container = ctk.CTkScrollableFrame(self, width=500, height=250)
        self.cat_container.pack(fill="both", expand=True, padx=20, pady=10)

    def _on_scan(self):
        self.scan_btn.configure(state="disabled", text="扫描中...")
        self.status_label.configure(text="正在扫描...")
        self.progress.set(0)
        self.update_idletasks()

        try:
            self._categories = self.cleaner.scan()
            self._render_categories()
            self.status_label.configure(text=f"扫描完成，共 {sum(c.total_size for c in self._categories)} 可清理")
            # 计算总大小显示
            total = sum(c.total_size for c in self._categories)
            self.status_label.configure(text=f"扫描完成，可清理 {format_bytes(total)}")
        except Exception as e:
            self.status_label.configure(text=f"扫描出错: {e}")
        finally:
            self.scan_btn.configure(state="normal", text="🔍 重新扫描")
            self.clean_btn.configure(state="normal")

    def _render_categories(self):
        for w in self.cat_container.winfo_children():
            w.destroy()
        self._checkboxes.clear()
        self._size_labels.clear()

        saved = self.config.get("clean_categories", {})

        for cat in self._categories:
            row = ctk.CTkFrame(self.cat_container, fg_color="transparent")
            row.pack(fill="x", pady=3)
            default_checked = saved.get(cat.key, True)
            var = ctk.BooleanVar(value=default_checked)
            cb = ctk.CTkCheckBox(row, text=cat.label, variable=var)
            cb.pack(side="left", padx=5)
            size_label = ctk.CTkLabel(row, text=format_bytes(cat.total_size), width=100)
            size_label.pack(side="right", padx=5)
            self._checkboxes[cat.key] = cb
            self._size_labels[cat.key] = size_label

    def _on_clean(self):
        selected = {key for key, cb in self._checkboxes.items() if cb.get()}
        if not selected:
            self.status_label.configure(text="请至少选择一项")
            return

        self.clean_btn.configure(state="disabled", text="清理中...")
        self.progress.set(0)
        self.status_label.configure(text="正在清理...")
        self.update_idletasks()

        try:
            freed, errors = self.cleaner.clean(selected)
            self.progress.set(1)

            # 更新配置
            total_cleaned = self.config.get("total_cleaned_bytes", 0) + freed
            self.config.set("total_cleaned_bytes", total_cleaned)
            self.config.set("last_optimization", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            msg = f"清理完成！释放 {format_bytes(freed)}"
            if errors:
                msg += f" ({len(errors)} 项跳过)"
            self.status_label.configure(text=msg)
        except Exception as e:
            self.status_label.configure(text=f"清理出错: {e}")
        finally:
            self.clean_btn.configure(state="normal", text="🧹 一键清理")
            # 重新扫描刷新
            self._on_scan()
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add cleaner UI tab"
```

---

### Task 10: UI — Startup Tab

**Files:** Create `ui/startup.py`

- [ ] **Step 1: Write startup.py**

```python
"""启动项管理 Tab."""

import customtkinter as ctk

from core.startup import StartupManager, StartupEntry
from utils.config import Config


class StartupFrame(ctk.CTkFrame):
    def __init__(self, master, config: Config, **kwargs):
        super().__init__(master, **kwargs)
        self.config = config
        self.manager = StartupManager()
        self._entries: list[StartupEntry] = []
        self._switches: dict[int, ctk.CTkSwitch] = {}
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ctk.CTkLabel(self, text="启动项管理", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_frame, text="🔄 刷新", command=self._refresh).pack(side="left", padx=5)
        ctk.CTkLabel(btn_frame, text="开关控制启用/禁用", font=ctk.CTkFont(size=11)).pack(side="right", padx=5)

        self.list_frame = ctk.CTkScrollableFrame(self, width=550, height=300)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def _refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self._switches.clear()

        try:
            self._entries = self.manager.get_entries()
            disabled_list = self.config.get("startup_disabled", [])

            for i, entry in enumerate(self._entries):
                row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)

                # 名称
                name_label = ctk.CTkLabel(row, text=entry.name, width=150, anchor="w")
                name_label.pack(side="left", padx=5)
                # 来源
                ctk.CTkLabel(row, text=entry.source, width=80,
                             font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
                # 命令（截断）
                cmd = entry.command
                if len(cmd) > 50:
                    cmd = cmd[:47] + "..."
                ctk.CTkLabel(row, text=cmd, font=ctk.CTkFont(size=10),
                             fg_color="gray20", corner_radius=4).pack(side="left", padx=5, fill="x", expand=True)

                # 开关
                is_enabled = entry.command not in disabled_list
                switch = ctk.CTkSwitch(
                    row, text="启用" if is_enabled else "禁用",
                    command=lambda e=entry, idx=i: self._toggle(idx),
                )
                if is_enabled:
                    switch.select()
                else:
                    switch.deselect()
                switch.pack(side="right", padx=5)
                self._switches[i] = switch

        except Exception as e:
            ctk.CTkLabel(self.list_frame, text=f"加载失败: {e}").pack()

    def _toggle(self, index: int):
        entry = self._entries[index]
        switch = self._switches[index]
        disabled = self.config.get("startup_disabled", [])

        if switch.get():
            self.manager.enable_entry(entry)
            if entry.command in disabled:
                disabled.remove(entry.command)
            switch.configure(text="启用")
        else:
            self.manager.disable_entry(entry)
            if entry.command not in disabled:
                disabled.append(entry.command)
            switch.configure(text="禁用")

        self.config.set("startup_disabled", disabled)
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add startup manager UI tab"
```

---

### Task 11: UI — Process Tab

**Files:** Create `ui/process.py`

- [ ] **Step 1: Write process.py**

```python
"""进程管理 Tab."""

import customtkinter as ctk
from tkinter import messagebox

from core.process import ProcessManager


class ProcessFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.manager = ProcessManager()
        self._procs: list[dict] = []
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ctk.CTkLabel(self, text="进程管理", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))

        # 顶部控制栏
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=20, pady=5)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        search_entry = ctk.CTkEntry(ctrl, placeholder_text="搜索进程名...",
                                     textvariable=self.search_var, width=200)
        search_entry.pack(side="left", padx=5)

        ctk.CTkButton(ctrl, text="🔄 刷新", width=80, command=self._refresh).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="❌ 结束进程", width=100,
                      fg_color="#c0392b", hover_color="#e74c3c",
                      command=self._kill_selected).pack(side="left", padx=5)

        # 列标题
        header = ctk.CTkFrame(self, fg_color="gray20")
        header.pack(fill="x", padx=20, pady=(10, 0))
        for text, width in [("名称", 150), ("PID", 70), ("CPU%", 70), ("内存", 80)]:
            ctk.CTkLabel(header, text=text, width=width,
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)

        # 列表
        self.list_frame = ctk.CTkScrollableFrame(self, width=550, height=300)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _refresh(self):
        self._procs = self.manager.get_processes()
        self._render(self._procs)

    def _filter(self):
        query = self.search_var.get().lower()
        if not query:
            self._render(self._procs)
            return
        filtered = [p for p in self._procs if query in p["name"].lower()]
        self._render(filtered)

    def _render(self, procs: list[dict]):
        for w in self.list_frame.winfo_children():
            w.destroy()

        for proc in procs[:100]:  # 限制显示前100条
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=proc["name"], width=150, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(row, text=str(proc["pid"]), width=70).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"{proc['cpu_percent']:.1f}", width=70).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"{proc['memory_mb']:.0f} MB", width=80).pack(side="left", padx=2)

    def _kill_selected(self):
        """由于 CustomTkinter 没有原生列表选择，使用弹窗输入 PID."""
        dialog = ctk.CTkInputDialog(
            title="结束进程",
            text="输入要结束的进程 PID:",
        )
        pid_str = dialog.get_input()
        if not pid_str:
            return
        try:
            pid = int(pid_str)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字 PID")
            return

        if self.manager.is_protected(pid):
            messagebox.showwarning("受保护", "这是系统关键进程，无法终止")
            return

        if self.manager.kill_process(pid):
            messagebox.showinfo("成功", f"进程 {pid} 已终止")
            self._refresh()
        else:
            messagebox.showerror("失败", f"无法终止进程 {pid}（可能需要管理员权限）")
```

- [ ] **Step 2: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: add process manager UI tab"
```

---

### Task 12: App Shell + Entry Point

**Files:** Create `app.py`, `main.py`

- [ ] **Step 1: Write app.py**

```python
"""主应用窗口：TabView 容器 + 全局线程管理."""

import customtkinter as ctk

from core.monitor import SystemMonitor
from utils.config import Config
from ui.dashboard import DashboardFrame
from ui.cleaner import CleanerFrame
from ui.startup import StartupFrame
from ui.process import ProcessFrame


class PerfBoostApp:
    def __init__(self):
        self.config = Config()
        self.monitor = SystemMonitor(interval=self.config.get("monitor_interval", 1))

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("PerfBoost - 系统性能优化")
        self.root.geometry("700x750")
        self.root.minsize(600, 600)

        self._build_ui()
        self.monitor.start()

    def _build_ui(self):
        ctk.CTkLabel(
            self.root,
            text="⚡ PerfBoost",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=(20, 0))
        ctk.CTkLabel(
            self.root,
            text="Windows 系统性能优化工具",
            font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 10))

        tabview = ctk.CTkTabview(self.root)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        tabs = ["📊 仪表盘", "🧹 清理", "🚀 启动项", "📋 进程"]
        for name in tabs:
            tabview.add(name)

        DashboardFrame(tabview.tab("📊 仪表盘"), self.monitor, self.config).pack(
            fill="both", expand=True)
        CleanerFrame(tabview.tab("🧹 清理"), self.config).pack(fill="both", expand=True)
        StartupFrame(tabview.tab("🚀 启动项"), self.config).pack(fill="both", expand=True)
        ProcessFrame(tabview.tab("📋 进程")).pack(fill="both", expand=True)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self.monitor.stop()
        self.root.destroy()
```

- [ ] **Step 2: Write main.py**

```python
"""PerfBoost 入口."""

import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import PerfBoostApp


def main():
    app = PerfBoostApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify the app starts**

```bash
cd E:/Projects/perfboost && python main.py
```
Expected: GUI 窗口出现，四个 Tab 可切换，仪表盘显示实时数据。

- [ ] **Step 4: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "feat: wire up app shell and entry point"
```

---

### Task 13: Final Polish — .gitignore and README

**Files:** Create `.gitignore`, update `README.md`

- [ ] **Step 1: Write .gitignore**

```gitignore
__pycache__/
*.py[cod]
*.so
*.egg-info/
dist/
build/
*.spec
.env
venv/
.venv/
*.log
```

- [ ] **Step 2: Write README.md**

```markdown
# PerfBoost

Windows 系统性能优化工具，基于 Python + CustomTkinter。

## 功能

- 📊 **仪表盘** — 实时 CPU/内存/磁盘/温度/网速监控
- 🧹 **清理** — 一键扫描清理临时文件、浏览器缓存等
- 🚀 **启动项** — 管理开机自启程序
- 📋 **进程** — 查看和结束进程

## 运行

```bash
pip install -r requirements.txt
python main.py
```

## 打包

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name PerfBoost main.py
```
```

- [ ] **Step 3: Commit**

```bash
cd E:/Projects/perfboost && git add -A && git commit -m "chore: add gitignore and README"
```

---

## Plan Self-Review

**Spec coverage check:**
- 仪表盘（CPU/内存/磁盘/温度/网速） → Task 4 + Task 8 ✅
- 垃圾清理（扫描 + 分类 + 清理 + 安全约束） → Task 5 + Task 9 ✅
- 启动项管理（注册表/启动文件夹 + 启用/禁用） → Task 6 + Task 10 ✅
- 进程管理（列表 + 终止 + 系统保护） → Task 7 + Task 11 ✅
- 配置持久化（JSON + 单例） → Task 3 ✅
- 错误处理（权限不足跳过、文件占用跳过） → 各 core 模块内处理 ✅
- V2 延后功能（暗色切换、国际化、自动优化等） → 未包含 ✅

**Placeholder scan:** 无 "TBD"、"TODO"、"implement later"。

**Type consistency:**
- `Config.get(key, default)` 签名一致 ✅
- `SystemMonitor.data_queue` 属性一致 ✅
- `JunkCleaner.scan()` → `list[CleanCategory]` ✅
- `StartupManager.get_entries()` → `list[StartupEntry]` ✅
- `ProcessManager.get_processes()` → `list[dict]` ✅
- `format_bytes(bytes)` 签名一致 ✅
