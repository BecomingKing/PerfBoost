"""通用工具函数."""

import os
import ctypes
from typing import Optional


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


def get_boot_time() -> Optional[float]:
    """返回系统开机时间戳，失败返回 None."""
    try:
        import psutil
        return psutil.boot_time()
    except Exception:
        return None


def get_theme_from_registry() -> str:
    """从 Windows 注册表读取系统主题，返回 "dark" 或 "light"."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except Exception:
        return "dark"


def relaunch_as_admin() -> None:
    """以管理员权限重新启动当前程序，然后退出当前进程."""
    import sys

    # 清理锁文件，避免新实例误判为重复运行
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    for fname in (".lock", ".show_signal"):
        fpath = os.path.join(script_dir, "data", fname)
        try:
            os.remove(fpath)
        except OSError:
            pass

    if getattr(sys, 'frozen', False):
        # PyInstaller 打包的 exe
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, "", None, 1,
        )
    else:
        # 源码运行
        script = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}"', None, 1,
        )

    sys.exit(0)


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
