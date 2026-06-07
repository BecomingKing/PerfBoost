"""系统硬件监控模块，封装 psutil 采样逻辑."""

import time
import threading
import queue

import psutil


class SystemMonitor:
    """后台线程持续采样系统指标，通过队列推送给UI."""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._queue = queue.Queue()
        self._thread = None
        self._running = False
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = time.time()

    @property
    def data_queue(self) -> queue.Queue:
        return self._queue

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while self._running:
            try:
                snapshot = self._sample()
                self._queue.put(snapshot)
            except Exception:
                self._queue.put({"error": "采样失败"})
            time.sleep(self.interval)

    def _sample(self) -> dict:
        now = time.time()

        cpu_percent = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory()

        # 磁盘 — 只收集有容量的分区
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                if usage.total == 0:
                    continue
                disks.append({
                    "mountpoint": part.mountpoint,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                })
            except PermissionError:
                continue

        # 网络速率
        net_io = psutil.net_io_counters()
        elapsed = max(now - self._last_net_time, 0.001)
        upload = (net_io.bytes_sent - self._last_net_io.bytes_sent) / elapsed
        download = (net_io.bytes_recv - self._last_net_io.bytes_recv) / elapsed
        self._last_net_io = net_io
        self._last_net_time = now

        return {
            "cpu_percent": cpu_percent,
            "memory_total": mem.total,
            "memory_used": mem.used,
            "memory_percent": mem.percent,
            "disks": disks,
            "net_upload": upload,
            "net_download": download,
        }
