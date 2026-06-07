"""PerfBoost 入口."""

__version__ = "1.0.0"

import sys
import os
import ctypes

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LOCK_FILE = os.path.join(DATA_DIR, ".lock")
SIGNAL_FILE = os.path.join(DATA_DIR, ".show_signal")


def _is_already_running():
    """检查是否已有实例在运行."""
    if not os.path.exists(LOCK_FILE):
        return False
    try:
        with open(LOCK_FILE, "r") as f:
            pid = int(f.read().strip())
        handle = ctypes.windll.kernel32.OpenProcess(0x100000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
    except (ValueError, OSError):
        pass
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass
    return False


def _signal_existing_instance():
    """通知已有实例显示窗口."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SIGNAL_FILE, "w") as f:
        f.write("show")


def _create_lock():
    """创建锁文件，写入当前 PID."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def _remove_lock():
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


def main():
    if _is_already_running():
        _signal_existing_instance()
        return
    _create_lock()
    try:
        from app import PerfBoostApp
        app = PerfBoostApp()
        app.run()
    finally:
        _remove_lock()


if __name__ == "__main__":
    main()
