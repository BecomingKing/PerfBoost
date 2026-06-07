"""测试 Cleaner 清理引擎."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestJunkCleaner:
    def test_scan_returns_list(self):
        from core.cleaner import JunkCleaner
        cleaner = JunkCleaner()
        result = cleaner.scan()
        assert isinstance(result, list)
        assert len(result) >= 3  # 至少有 temp, browser_cache, recycle_bin

    def test_scan_categories_have_keys(self):
        from core.cleaner import JunkCleaner
        cleaner = JunkCleaner()
        result = cleaner.scan()
        keys = {c.key for c in result}
        assert "temp" in keys
        assert "browser_cache" in keys
        assert "recycle_bin" in keys

    def test_clean_returns_tuple(self):
        from core.cleaner import JunkCleaner
        cleaner = JunkCleaner()
        cleaner.scan()
        result = cleaner.clean({"temp", "browser_cache"})
        assert len(result) == 3
        assert isinstance(result[0], int)

    def test_clean_empty_keys(self):
        from core.cleaner import JunkCleaner
        cleaner = JunkCleaner()
        cleaner.scan()
        freed, errors, skipped = cleaner.clean(set())
        assert isinstance(freed, int)
