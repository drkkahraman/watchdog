"""Tests for DockerManager communication and stats calculation."""

from unittest.mock import patch

from watchdog.core.docker_manager import DockerManager


def test_docker_manager_stats_calculation():
    manager = DockerManager()

    raw_stats = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 500000000},
            "system_cpu_usage": 10000000000,
            "online_cpus": 4,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 400000000},
            "system_cpu_usage": 9000000000,
        },
        "memory_stats": {
            "usage": 204800000,
            "limit": 1024000000,
            "stats": {"cache": 4800000},
        },
        "networks": {
            "eth0": {"rx_bytes": 1024, "tx_bytes": 2048}
        },
        "blkio_stats": {
            "io_service_bytes_recursive": [
                {"op": "Read", "value": 5000},
                {"op": "Write", "value": 3000}
            ]
        },
        "pids_stats": {"current": 8}
    }

    stats = manager._calculate_stats(raw_stats)
    # CPU: (100000000 / 1000000000) * 4 * 100 = 40.0%
    assert stats.cpu_percent == 40.0
    # Memory: 200000000 / 1024000000 * 100 = 19.53%
    assert 19.0 <= stats.memory_percent <= 20.0
    assert stats.net_rx_bytes == 1024
    assert stats.net_tx_bytes == 2048
    assert stats.block_read_bytes == 5000
    assert stats.block_write_bytes == 3000
    assert stats.pids == 8


def test_docker_manager_disconnected_fallback():
    with patch("docker.from_env", side_effect=Exception("Connection refused")):
        manager = DockerManager()
        assert manager.is_connected is False
        summary = manager.get_system_summary()
        assert summary["connected"] is False
        assert manager.list_containers() == []
