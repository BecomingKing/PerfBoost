"""测试磁盘分析扫描模块."""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFileEntry:
    """测试 FileEntry 数据类."""

    def test_fileentry_fields(self):
        from core.disk_analyzer import FileEntry
        entry = FileEntry(name="test.txt", path=r"C:\test\test.txt", size=1024, is_dir=False)
        assert entry.name == "test.txt"
        assert entry.path == r"C:\test\test.txt"
        assert entry.size == 1024
        assert entry.is_dir is False

    def test_fileentry_is_dir(self):
        from core.disk_analyzer import FileEntry
        entry = FileEntry(name="subdir", path=r"C:\test\subdir", size=0, is_dir=True)
        assert entry.is_dir is True


class TestDiskScanner:
    """测试 DiskScanner 扫描功能."""

    def _make_temp_tree(self):
        """创建一个临时目录树结构用于测试：
        tmpdir/
          file1.txt      100 bytes
          file2.txt      200 bytes
          subdir/
            file3.txt    50 bytes
        """
        tmpdir = tempfile.mkdtemp()
        # 文件1: 100字节
        with open(os.path.join(tmpdir, "file1.txt"), "wb") as f:
            f.write(b"A" * 100)
        # 文件2: 200字节
        with open(os.path.join(tmpdir, "file2.txt"), "wb") as f:
            f.write(b"B" * 200)
        # 子目录 + 文件3: 50字节
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        with open(os.path.join(subdir, "file3.txt"), "wb") as f:
            f.write(b"C" * 50)
        return tmpdir

    def test_scan_returns_list(self):
        from core.disk_analyzer import DiskScanner
        scanner = DiskScanner()
        tmpdir = self._make_temp_tree()
        try:
            entries = scanner.scan(tmpdir)
            assert isinstance(entries, list)
            assert len(entries) > 0
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_scan_all_entries_have_required_fields(self):
        from core.disk_analyzer import DiskScanner
        scanner = DiskScanner()
        tmpdir = self._make_temp_tree()
        try:
            entries = scanner.scan(tmpdir)
            for entry in entries:
                assert hasattr(entry, "name")
                assert hasattr(entry, "path")
                assert hasattr(entry, "size")
                assert hasattr(entry, "is_dir")
                assert isinstance(entry.name, str)
                assert isinstance(entry.path, str)
                assert isinstance(entry.size, int)
                assert isinstance(entry.is_dir, bool)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_scan_returns_correct_count(self):
        from core.disk_analyzer import DiskScanner
        scanner = DiskScanner()
        tmpdir = self._make_temp_tree()
        try:
            entries = scanner.scan(tmpdir)
            files = [e for e in entries if not e.is_dir]
            dirs = [e for e in entries if e.is_dir]
            # 2个顶层文件: file1, file2（file3 在 subdir 内部）
            assert len(files) == 2
            # 1个子目录: subdir
            assert len(dirs) == 1
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_total_size_matches(self):
        from core.disk_analyzer import DiskScanner
        scanner = DiskScanner()
        tmpdir = self._make_temp_tree()
        try:
            entries = scanner.scan(tmpdir)
            # 所有条目（文件和目录）恰好覆盖目录总大小
            total = sum(e.size for e in entries)
            # file1(100) + file2(200) + subdir(50) = 350
            assert total == 350
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_scan_empty_directory(self):
        from core.disk_analyzer import DiskScanner
        scanner = DiskScanner()
        tmpdir = tempfile.mkdtemp()
        try:
            entries = scanner.scan(tmpdir)
            assert entries == []
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_scan_nonexistent_path(self):
        from core.disk_analyzer import DiskScanner
        scanner = DiskScanner()
        entries = scanner.scan(r"C:\__nonexistent_path_xyz__")
        assert entries == []

    def test_progress_callback(self):
        from core.disk_analyzer import DiskScanner
        scanner = DiskScanner()
        tmpdir = self._make_temp_tree()
        called_paths = []
        try:
            entries = scanner.scan(tmpdir, on_progress=lambda p: called_paths.append(p))
            assert len(entries) > 0
            # progress 应该至少被调用一次
            assert len(called_paths) >= 1
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
