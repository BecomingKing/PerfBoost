"""测试 helpers 工具函数."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import format_bytes, is_admin, is_safe_path, get_boot_time, get_theme_from_registry


class TestFormatBytes:
    def test_zero(self):
        assert format_bytes(0) == "0.0 B"

    def test_bytes(self):
        assert "B" in format_bytes(500)

    def test_kb(self):
        result = format_bytes(2048)
        assert "KB" in result

    def test_mb(self):
        result = format_bytes(5 * 1024 * 1024)
        assert "MB" in result

    def test_negative(self):
        result = format_bytes(-500)
        assert "B" in result


class TestIsAdmin:
    def test_returns_bool(self):
        assert isinstance(is_admin(), bool)


class TestIsSafePath:
    def test_protected_system32(self):
        assert not is_safe_path(r"C:\Windows\System32\something.dll")

    def test_safe_temp(self):
        assert is_safe_path(r"C:\Users\Test\AppData\Local\Temp\file.tmp")

    def test_protected_program_files(self):
        assert not is_safe_path(r"C:\Program Files\MyApp\app.exe")


class TestBootTime:
    def test_returns_float_or_none(self):
        result = get_boot_time()
        assert result is None or isinstance(result, float)


class TestThemeFromRegistry:
    def test_returns_string(self):
        result = get_theme_from_registry()
        assert result in ("dark", "light")
