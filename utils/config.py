"""配置持久化模块，读写 %APPDATA%/PerfBoost/config.json."""

import json
import os
from typing import Any

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG: dict[str, Any] = {
    "clean_categories": {
        "temp": True,
        "browser_cache": True,
        "recycle_bin": True,
        "crash_dumps": True,
        "system_temp": False,
        "windows_logs": False,
        "thumbnails": False,
    },
    "monitor_interval": 1,
    "startup_disabled": [],
    "last_optimization": None,
    "total_cleaned_bytes": 0,
    "theme": "system",
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
