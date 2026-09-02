"""Tests for SystemMonitor host metrics."""

from unittest.mock import MagicMock, patch

from watchdog_tui.core.system_monitor import SystemMonitor


def test_system_monitor_get_stats():
    monitor = SystemMonitor()
    stats = monitor.get_stats()

    assert stats.cpu_count >= 1
    assert 0.0 <= stats.cpu_percent <= 100.0
    assert stats.memory_total >= 0
    assert stats.disk_total >= 0
    assert stats.uptime_seconds >= 0


def test_system_monitor_mocked_values():
    monitor = SystemMonitor()

    with patch("psutil.cpu_percent", return_value=42.5), \
         patch("psutil.virtual_memory") as mock_mem, \
         patch("psutil.disk_usage") as mock_disk:

        mock_mem.return_value = MagicMock(
            total=16000000000,
            used=8000000000,
            percent=50.0
        )
        mock_disk.return_value = MagicMock(
            total=500000000000,
            used=250000000000,
            percent=50.0
        )

        stats = monitor.get_stats()
        assert stats.cpu_percent == 42.5
        assert stats.memory_percent == 50.0
        assert stats.disk_percent == 50.0
