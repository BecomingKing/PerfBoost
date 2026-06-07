"""测试 Config 配置模块."""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfigDefault:
    def test_default_theme(self):
        from utils.config import DEFAULT_CONFIG
        assert DEFAULT_CONFIG.get("theme") == "system"

    def test_default_clean_categories(self):
        from utils.config import DEFAULT_CONFIG
        cats = DEFAULT_CONFIG.get("clean_categories", {})
        assert "temp" in cats
        assert cats["temp"] is True
        assert cats["windows_logs"] is False


class TestConfigSingleton:
    def test_singleton(self):
        from utils.config import Config
        a = Config()
        b = Config()
        assert a is b

    def test_get_set(self):
        from utils.config import Config
        cfg = Config()
        cfg.set("test_key", "test_value")
        assert cfg.get("test_key") == "test_value"

    def test_get_default(self):
        from utils.config import Config
        cfg = Config()
        assert cfg.get("nonexistent", "fallback") == "fallback"
