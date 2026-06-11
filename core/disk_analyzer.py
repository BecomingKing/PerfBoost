"""磁盘目录扫描模块 — 递归扫描目录并返回 FileEntry 列表."""

import os
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class FileEntry:
    """文件/目录条目."""
    name: str      # 文件或目录名
    path: str      # 完整路径
    size: int      # 字节数
    is_dir: bool   # True=目录, False=文件


class DiskScanner:
    """递归扫描目录，返回所有文件和子目录的大小信息."""

    def scan(
        self,
        path: str,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> list[FileEntry]:
        """扫描指定路径，返回 FileEntry 列表（仅直接子项）。

        Args:
            path: 要扫描的根目录路径
            on_progress: 每扫描完一个子目录时的回调，传入当前路径

        Returns:
            FileEntry 列表，文件按大小降序排列；路径不存在或无权限时返回空列表
        """
        if not os.path.isdir(path):
            return []

        entries: list[FileEntry] = []

        try:
            with os.scandir(path) as it:
                for item in it:
                    try:
                        if item.is_dir(follow_symlinks=False):
                            size = self._dir_size(item.path, on_progress)
                            entries.append(FileEntry(
                                name=item.name,
                                path=item.path,
                                size=size,
                                is_dir=True,
                            ))
                            if on_progress:
                                on_progress(item.path)
                        elif item.is_file(follow_symlinks=False):
                            stat = item.stat()
                            entries.append(FileEntry(
                                name=item.name,
                                path=item.path,
                                size=stat.st_size,
                                is_dir=False,
                            ))
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            return []

        # 按大小降序排列
        entries.sort(key=lambda e: e.size, reverse=True)
        return entries

    def _dir_size(
        self,
        path: str,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> int:
        """递归计算目录总大小（字节）。"""
        total = 0
        try:
            with os.scandir(path) as it:
                for item in it:
                    try:
                        if item.is_file(follow_symlinks=False):
                            total += item.stat().st_size
                        elif item.is_dir(follow_symlinks=False):
                            total += self._dir_size(item.path, on_progress)
                            if on_progress:
                                on_progress(item.path)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass
        return total
