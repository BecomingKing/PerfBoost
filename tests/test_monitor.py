"""测试 Monitor 采样模块."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSystemMonitor:
    def test_creates_queue(self):
        from core.monitor import SystemMonitor
        m = SystemMonitor(interval=1)
        assert m.data_queue is not None

    def test_sample_structure(self):
        from core.monitor import SystemMonitor
        m = SystemMonitor(interval=1)
        data = m._sample()
        assert isinstance(data, dict)
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "memory_total" in data
        assert "memory_used" in data
        assert "disks" in data
        assert "net_upload" in data
        assert "net_download" in data

    def test_cpu_percent_range(self):
        from core.monitor import SystemMonitor
        m = SystemMonitor(interval=1)
        data = m._sample()
        assert 0 <= data["cpu_percent"] <= 100

    def test_memory_percent_range(self):
        from core.monitor import SystemMonitor
        m = SystemMonitor(interval=1)
        data = m._sample()
        assert 0 <= data["memory_percent"] <= 100

    def test_disk_list(self):
        from core.monitor import SystemMonitor
        m = SystemMonitor(interval=1)
        data = m._sample()
        for disk in data["disks"]:
            assert "mountpoint" in disk
            assert "total" in disk
            assert "used" in disk
            assert "percent" in disk
