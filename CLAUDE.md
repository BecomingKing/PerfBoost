# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app
python main.py

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_config.py -v

# Run a single test class or method
pytest tests/test_helpers.py::TestFormatBytes -v
pytest tests/test_helpers.py::TestIsSafePath::test_protected_system32 -v

# Package into a standalone exe
pip install pyinstaller
pyinstaller --onefile --windowed --name PerfBoost main.py
```

## Architecture

```
main.py          → Entry point, single-instance enforcement via PID lock file (data/.lock)
app.py           → PerfBoostApp: main window, sidebar nav, page switching, monitor polling
ui/              → CTkFrame subclasses, one per tab
core/            → Business logic, no tkinter imports
utils/           → Config singleton + pure helper functions
```

### Layers

1. **`main.py`** — Uses a PID lock file (`data/.lock`) and signal file (`data/.show_signal`) for single-instance enforcement. On double-launch, signals the existing instance to restore its window.
2. **`app.py` / `PerfBoostApp`** — Creates the CTk root window, sidebar navigation with per-tab highlight state, a background `SystemMonitor` thread, and a polling loop via `root.after(1000, …)` that feeds monitor data to the dashboard. Handles theme switching and tray minimize/restore.
3. **`ui/*.py`** — Each file is a `ctk.CTkFrame` subclass. Pages are instantiated once at startup and shown/hidden via `pack_forget()`/`pack()`. No pages are destroyed during navigation.
4. **`core/*.py`** — Pure logic modules with no UI dependency. `SystemMonitor` runs a daemon thread pushing data into a `queue.Queue` (though `app.py` calls `_sample()` directly instead of consuming the queue). `JunkCleaner` scans file categories and uses `MoveFileEx` + `MOVEFILE_DELAY_UNTIL_REBOOT` for locked files. `StartupManager` reads/writes the Windows Registry (HKCU/HKLM Run keys) and Startup folders, with JSON backup before disabling. `ProcessManager` wraps psutil with a `PROTECTED_NAMES` blocklist.
5. **`utils/config.py`** — `Config` is a singleton. Data is persisted to `data/config.json` in the project root. Keys are merged with `DEFAULT_CONFIG` on load so new defaults appear automatically. `config.set()` auto-saves; `config.get()` uses lazy one-time load.

### Key design patterns

- **Admin escalation**: `utils/helpers.py:relaunch_as_admin()` cleans lock files then re-invokes via `ShellExecuteW` with `"runas"`. The cleaner UI checks `is_admin()` before cleaning admin-required categories and offers to restart elevated.
- **Theme**: `ctk.set_appearance_mode()` is set at startup from `config.theme`. When "system", `get_theme_from_registry()` reads `AppsUseLightTheme` from the Windows registry.
- **Tests**: Tests use manual `sys.path.insert` to find modules (no editable install). Run on Windows only — many helpers and core modules call Win32 APIs.
