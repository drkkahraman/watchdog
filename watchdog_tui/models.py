"""Data models for Watchdog."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContainerPort:
    """Port mapping definition."""
    host_ip: str
    host_port: str
    container_port: str
    protocol: str = "tcp"

    def __str__(self) -> str:
        if self.host_port:
            return f"{self.host_ip}:{self.host_port}->{self.container_port}/{self.protocol}"
        return f"{self.container_port}/{self.protocol}"


@dataclass
class ContainerStats:
    """Live resource metrics for a container."""
    cpu_percent: float = 0.0
    memory_usage: int = 0
    memory_limit: int = 0
    memory_percent: float = 0.0
    net_rx_bytes: int = 0
    net_tx_bytes: int = 0
    block_read_bytes: int = 0
    block_write_bytes: int = 0
    pids: int = 0


@dataclass
class ContainerInfo:
    """Information and state of a Docker container."""
    id: str
    short_id: str
    name: str
    image: str
    status: str  # running, exited, paused, restarting, etc.
    state: str
    health: str | None = None  # healthy, unhealthy, starting, none
    created_at: str = ""
    uptime: str = ""
    command: str = ""
    ports: list[ContainerPort] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    stats: ContainerStats = field(default_factory=ContainerStats)
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        return self.status.lower() == "running"

    @property
    def is_paused(self) -> bool:
        return self.status.lower() == "paused"


@dataclass
class ProxyRoute:
    """Detected Reverse Proxy or Port Routing."""
    container_name: str
    container_id: str
    service_type: str  # Traefik, Caddy, NPM, Port Mapping, Cloudflare
    rule_or_domain: str
    target_port: str
    entrypoint_or_host: str
    tls_enabled: bool = False
    details: str = ""


@dataclass
class SystemStats:
    """Host machine resource statistics."""
    cpu_percent: float = 0.0
    cpu_count: int = 1
    cpu_freq_mhz: float = 0.0
    memory_total: int = 0
    memory_used: int = 0
    memory_percent: float = 0.0
    swap_total: int = 0
    swap_used: int = 0
    swap_percent: float = 0.0
    disk_total: int = 0
    disk_used: int = 0
    disk_percent: float = 0.0
    net_sent_speed: float = 0.0  # bytes/sec
    net_recv_speed: float = 0.0  # bytes/sec
    uptime_seconds: float = 0.0
    docker_version: str = ""
    docker_containers_total: int = 0
    docker_containers_running: int = 0
    docker_containers_paused: int = 0
    docker_containers_stopped: int = 0
    docker_images_count: int = 0
