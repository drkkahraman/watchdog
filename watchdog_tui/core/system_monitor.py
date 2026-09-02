"""Host system metrics collector using psutil."""

import time

import psutil

from watchdog_tui.models import SystemStats


class SystemMonitor:
    """Collects host machine performance and capacity statistics."""

    def __init__(self) -> None:
        self._last_net_time: float = time.time()
        self._last_net_sent: int = 0
        self._last_net_recv: int = 0

        # Initialize network baseline
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                self._last_net_sent = net_io.bytes_sent
                self._last_net_recv = net_io.bytes_recv
        except Exception:
            pass

        # Prime cpu_percent
        psutil.cpu_percent(interval=None)

    def get_stats(self) -> SystemStats:
        """Gather current snapshot of host system metrics."""
        stats = SystemStats()

        # CPU
        try:
            stats.cpu_percent = psutil.cpu_percent(interval=None)
            stats.cpu_count = psutil.cpu_count(logical=True) or 1
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                stats.cpu_freq_mhz = cpu_freq.current
        except Exception:
            pass

        # Memory & Swap
        try:
            mem = psutil.virtual_memory()
            stats.memory_total = mem.total
            stats.memory_used = mem.used
            stats.memory_percent = mem.percent

            swap = psutil.swap_memory()
            stats.swap_total = swap.total
            stats.swap_used = swap.used
            stats.swap_percent = swap.percent
        except Exception:
            pass

        # Disk
        try:
            disk = psutil.disk_usage("/")
            stats.disk_total = disk.total
            stats.disk_used = disk.used
            stats.disk_percent = disk.percent
        except Exception:
            pass

        # Network Speeds
        try:
            now = time.time()
            net_io = psutil.net_io_counters()
            if net_io and self._last_net_time > 0:
                elapsed = max(0.1, now - self._last_net_time)
                stats.net_sent_speed = max(0.0, (net_io.bytes_sent - self._last_net_sent) / elapsed)
                stats.net_recv_speed = max(0.0, (net_io.bytes_recv - self._last_net_recv) / elapsed)

                self._last_net_sent = net_io.bytes_sent
                self._last_net_recv = net_io.bytes_recv
                self._last_net_time = now
        except Exception:
            pass

        # Uptime
        try:
            stats.uptime_seconds = time.time() - psutil.boot_time()
        except Exception:
            pass

        return stats
