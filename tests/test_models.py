"""Tests for Watchdog data models."""

from watchdog_tui.models import ContainerInfo, ContainerPort, ContainerStats, ProxyRoute, SystemStats


def test_container_port_str():
    port1 = ContainerPort(host_ip="0.0.0.0", host_port="8080", container_port="80", protocol="tcp")
    assert str(port1) == "0.0.0.0:8080->80/tcp"

    port2 = ContainerPort(host_ip="", host_port="", container_port="3306", protocol="tcp")
    assert str(port2) == "3306/tcp"


def test_container_info_properties():
    info_running = ContainerInfo(
        id="1234567890abcdef",
        short_id="1234567890ab",
        name="web_app",
        image="nginx:alpine",
        status="running",
        state="running",
        health="healthy",
    )
    assert info_running.is_running is True
    assert info_running.is_paused is False

    info_paused = ContainerInfo(
        id="abcdef1234567890",
        short_id="abcdef123456",
        name="db_app",
        image="postgres:15",
        status="paused",
        state="paused",
    )
    assert info_paused.is_running is False
    assert info_paused.is_paused is True


def test_proxy_route_and_system_stats():
    route = ProxyRoute(
        container_name="n8n",
        container_id="59ce21e06fe0",
        service_type="Traefik",
        rule_or_domain="Host(`n8n.example.com`)",
        target_port="5678",
        entrypoint_or_host="websecure",
        tls_enabled=True,
    )
    assert route.service_type == "Traefik"
    assert route.tls_enabled is True

    sys_stats = SystemStats(cpu_percent=12.5, memory_percent=45.0, disk_percent=33.3)
    assert sys_stats.cpu_percent == 12.5
