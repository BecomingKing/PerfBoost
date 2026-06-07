"""进程管理模块."""

import ctypes
import subprocess
from ctypes import wintypes

import psutil

# ── Win32 API 常量 ──
WM_CLOSE = 0x0010

# 不弹黑窗
_CREATE_NO_WINDOW = 0x08000000


def _find_windows_for_pid(pid: int) -> list[int]:
    """查找属于指定进程的所有顶层窗口句柄（含不可见窗口）."""
    windows: list[int] = []

    try:
        user32 = ctypes.windll.user32
    except (AttributeError, OSError):
        return windows

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def enum_callback(hwnd: int, lParam: int) -> bool:
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value == lParam and user32.IsWindow(hwnd):
            windows.append(hwnd)
        return True

    callback = WNDENUMPROC(enum_callback)
    user32.EnumWindows(callback, wintypes.LPARAM(pid))
    return windows


def _send_wm_close_to_windows(pid: int) -> bool:
    """向进程的所有窗口发送 WM_CLOSE。

    返回 True 表示找到了窗口并发送了消息。
    """
    windows = _find_windows_for_pid(pid)
    if not windows:
        return False

    user32 = ctypes.windll.user32
    for hwnd in windows:
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    return True


def _taskkill_graceful(pid: int) -> bool:
    """通过 Windows taskkill 发送关闭信号（等效于 WM_CLOSE）。

    返回 True 表示进程已被成功终止。
    """
    try:
        result = subprocess.run(
            ["taskkill", "/PID", str(pid)],
            capture_output=True,
            timeout=10,
            creationflags=_CREATE_NO_WINDOW,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def _taskkill_force_tree(pid: int) -> bool:
    """强制终止进程及其所有子进程。

    返回 True 表示成功。
    """
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            timeout=10,
            creationflags=_CREATE_NO_WINDOW,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


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
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        procs.sort(key=lambda p: p["memory_mb"], reverse=True)
        return procs

    def kill_process(self, pid: int) -> tuple[bool, str]:
        """终止指定进程。四层策略：WM_CLOSE → taskkill 优雅 → terminate 进程树 → taskkill 强杀。

        返回 (成功, 消息).
        """
        try:
            proc = psutil.Process(pid)
            pname = proc.name()

            if pname in self.PROTECTED_NAMES:
                return False, f"{pname} 是系统关键进程，无法终止"

            # ── 策略 1: WM_CLOSE 直接发消息（最快）──
            if _send_wm_close_to_windows(pid):
                try:
                    proc.wait(timeout=3)
                    return True, f"{pname} 已正常关闭"
                except psutil.TimeoutExpired:
                    pass

            # ── 策略 2: taskkill 优雅关闭（Windows 原生，覆盖 UWP/多进程等边界情况）──
            try:
                if _taskkill_graceful(pid):
                    try:
                        proc.wait(timeout=5)
                        return True, f"{pname} 已正常关闭"
                    except psutil.TimeoutExpired:
                        pass
            except psutil.NoSuchProcess:
                return True, "进程已不存在"

            # 确认进程是否还活着
            try:
                if not proc.is_running():
                    return True, "进程已不存在"
            except psutil.NoSuchProcess:
                return True, "进程已不存在"

            # ── 策略 3: terminate() 进程树 ──
            children = proc.children(recursive=True)
            self._terminate_tree(proc, children)
            gone, alive = psutil.wait_procs([proc] + children, timeout=4)
            if not alive:
                return True, f"{pname} 已终止"

            # ── 策略 4: taskkill /F /T 强杀整个进程树 ──
            if _taskkill_force_tree(pid):
                return True, f"{pname} 已强制终止（⚠ 可能导致程序下次无法正常启动）"

            return False, f"无法终止 {pname}（进程未响应）"

        except psutil.NoSuchProcess:
            return True, "进程已不存在"
        except psutil.AccessDenied:
            return False, "权限不足，请以管理员身份运行后重试"

    def _terminate_tree(self, proc: psutil.Process, children: list[psutil.Process]) -> None:
        """终止进程树：先子进程，后父进程."""
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            pass

    def is_protected(self, pid: int) -> bool:
        """检查是否为受保护的系统进程."""
        try:
            proc = psutil.Process(pid)
            return proc.name() in self.PROTECTED_NAMES
        except psutil.NoSuchProcess:
            return False
