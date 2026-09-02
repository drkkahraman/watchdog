"""Docker API Manager and Container Controller."""

from typing import Any

import docker
from docker.errors import APIError, DockerException, NotFound

from watchdog.models import ContainerInfo, ContainerPort, ContainerStats


class DockerManager:
    """Handles communication with the Docker Daemon."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url
        self.client: docker.DockerClient | None = None
        self.is_connected: bool = False
        self.connection_error: str | None = None
        self._cached_stats: dict[str, ContainerStats] = {}
        self.connect()

    def connect(self) -> bool:
        """Establish connection with Docker Daemon."""
        try:
            if self.base_url:
                self.client = docker.DockerClient(base_url=self.base_url)
            else:
                self.client = docker.from_env()

            self.client.ping()
            self.is_connected = True
            self.connection_error = None
            return True
        except DockerException as e:
            self.is_connected = False
            self.connection_error = str(e)
            self.client = None
            return False
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)
            self.client = None
            return False

    def get_system_summary(self) -> dict[str, Any]:
        """Fetch Docker engine overview."""
        if not self.is_connected or not self.client:
            return {
                "connected": False,
                "error": self.connection_error or "Not connected",
                "version": "N/A",
                "containers_total": 0,
                "containers_running": 0,
                "containers_paused": 0,
                "containers_stopped": 0,
                "images_count": 0,
            }

        try:
            info = self.client.info()
            version_info = self.client.version()
            version_str = version_info.get("Version", "Unknown")

            return {
                "connected": True,
                "error": None,
                "version": version_str,
                "containers_total": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "containers_paused": info.get("ContainersPaused", 0),
                "containers_stopped": info.get("ContainersStopped", 0),
                "images_count": info.get("Images", 0),
                "server_version": info.get("ServerVersion", version_str),
                "os": info.get("OperatingSystem", "Linux"),
                "driver": info.get("Driver", "overlay2"),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "version": "Error",
                "containers_total": 0,
                "containers_running": 0,
                "containers_paused": 0,
                "containers_stopped": 0,
                "images_count": 0,
            }

    def list_containers(self, all_containers: bool = True) -> list[ContainerInfo]:
        """List all containers with normalized metadata."""
        if not self.is_connected or not self.client:
            # Try to reconnect
            if not self.connect():
                return []

        try:
            containers = self.client.containers.list(all=all_containers)
            result: list[ContainerInfo] = []

            for c in containers:
                attrs = c.attrs or {}
                state = attrs.get("State", {})
                status = state.get("Status", c.status)

                # Health
                health_info = state.get("Health", {})
                health_status = health_info.get("Status") if health_info else None

                # Clean name
                name = c.name.lstrip("/")

                # Image name
                image_name = "<none>"
                if c.image and c.image.tags:
                    image_name = c.image.tags[0]
                elif c.image and c.image.short_id:
                    image_name = c.image.short_id
                elif "Config" in attrs and "Image" in attrs["Config"]:
                    image_name = attrs["Config"]["Image"]

                # Parse Port Mappings
                ports = self._parse_ports(attrs)

                # Fetch or use cached stats
                stats = self._cached_stats.get(c.id, ContainerStats())

                # Clean uptime string
                uptime = self._extract_uptime(state)

                c_info = ContainerInfo(
                    id=c.id,
                    short_id=c.short_id,
                    name=name,
                    image=image_name,
                    status=status,
                    state=state.get("Status", status),
                    health=health_status,
                    created_at=attrs.get("Created", ""),
                    uptime=uptime,
                    command=" ".join(c.attrs.get("Config", {}).get("Cmd") or []) if c.attrs.get("Config") else "",
                    ports=ports,
                    labels=attrs.get("Config", {}).get("Labels") or {},
                    stats=stats,
                    raw_data=attrs
                )
                result.append(c_info)

            # Sort by running first, then name
            result.sort(key=lambda x: (not x.is_running, x.name.lower()))
            return result
        except Exception:
            return []

    def update_container_stats(self, container_id: str) -> ContainerStats | None:
        """Fetch real-time CPU, RAM, and I/O metrics for a container."""
        if not self.is_connected or not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)
            if container.status != "running":
                stats = ContainerStats()
                self._cached_stats[container_id] = stats
                return stats

            raw_stats = container.stats(stream=False)
            stats = self._calculate_stats(raw_stats)
            self._cached_stats[container_id] = stats
            return stats
        except Exception:
            return None

    def update_all_running_stats(self) -> dict[str, ContainerStats]:
        """Update metrics for all running containers."""
        if not self.is_connected or not self.client:
            return {}

        try:
            containers = self.client.containers.list(all=False)
            for c in containers:
                try:
                    raw_stats = c.stats(stream=False)
                    self._cached_stats[c.id] = self._calculate_stats(raw_stats)
                except Exception:
                    pass
            return self._cached_stats
        except Exception:
            return {}

    def _calculate_stats(self, raw: dict[str, Any]) -> ContainerStats:
        """Calculate percentage and byte metrics from raw Docker stats JSON."""
        stats = ContainerStats()
        if not raw:
            return stats

        # CPU calculation
        try:
            cpu_stats = raw.get("cpu_stats", {})
            precpu_stats = raw.get("precpu_stats", {})

            cpu_usage = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            precpu_usage = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)

            system_cpu_usage = cpu_stats.get("system_cpu_usage", 0)
            system_precpu_usage = precpu_stats.get("system_cpu_usage", 0)

            cpu_delta = cpu_usage - precpu_usage
            system_delta = system_cpu_usage - system_precpu_usage

            online_cpus = cpu_stats.get("online_cpus")
            if not online_cpus:
                percpu = cpu_stats.get("cpu_usage", {}).get("percpu_usage")
                online_cpus = len(percpu) if percpu else 1

            if system_delta > 0 and cpu_delta > 0:
                stats.cpu_percent = round((cpu_delta / system_delta) * online_cpus * 100.0, 2)
            else:
                stats.cpu_percent = 0.0
        except Exception:
            stats.cpu_percent = 0.0

        # Memory calculation
        try:
            mem_stats = raw.get("memory_stats", {})
            usage = mem_stats.get("usage", 0)
            # Adjust for cache / inactive_file in cgroups v1 / v2 if present
            stats_dict = mem_stats.get("stats", {})
            cache = stats_dict.get("inactive_file", stats_dict.get("cache", 0))
            real_usage = max(0, usage - cache) if (usage - cache) > 0 else usage
            limit = mem_stats.get("limit", 0)

            stats.memory_usage = real_usage
            stats.memory_limit = limit
            if limit > 0:
                stats.memory_percent = round((real_usage / limit) * 100.0, 2)
            else:
                stats.memory_percent = 0.0
        except Exception:
            pass

        # Network I/O
        try:
            networks = raw.get("networks", {})
            rx_bytes = 0
            tx_bytes = 0
            for net in networks.values():
                rx_bytes += net.get("rx_bytes", 0)
                tx_bytes += net.get("tx_bytes", 0)
            stats.net_rx_bytes = rx_bytes
            stats.net_tx_bytes = tx_bytes
        except Exception:
            pass

        # Block I/O
        try:
            blkio = raw.get("blkio_stats", {}).get("io_service_bytes_recursive") or []
            read_bytes = 0
            write_bytes = 0
            for entry in blkio:
                op = entry.get("op", "").lower()
                val = entry.get("value", 0)
                if op == "read":
                    read_bytes += val
                elif op == "write":
                    write_bytes += val
            stats.block_read_bytes = read_bytes
            stats.block_write_bytes = write_bytes
        except Exception:
            pass

        # PIDs
        try:
            stats.pids = raw.get("pids_stats", {}).get("current", 0)
        except Exception:
            pass

        return stats

    def _parse_ports(self, attrs: dict[str, Any]) -> list[ContainerPort]:
        """Extract port mappings from container attributes."""
        ports: list[ContainerPort] = []
        network_settings = attrs.get("NetworkSettings", {})
        ports_dict = network_settings.get("Ports") or {}

        for container_p, host_bindings in ports_dict.items():
            parts = container_p.split("/")
            c_port = parts[0]
            protocol = parts[1] if len(parts) > 1 else "tcp"

            if host_bindings:
                for binding in host_bindings:
                    host_ip = binding.get("HostIp", "0.0.0.0")
                    host_port = binding.get("HostPort", "")
                    ports.append(
                        ContainerPort(
                            host_ip=host_ip,
                            host_port=host_port,
                            container_port=c_port,
                            protocol=protocol
                        )
                    )
            else:
                # Exposed container port without direct host binding
                ports.append(
                    ContainerPort(
                        host_ip="",
                        host_port="",
                        container_port=c_port,
                        protocol=protocol
                    )
                )
        return ports

    def _extract_uptime(self, state: dict[str, Any]) -> str:
        """Extract a readable uptime / status message."""
        status = state.get("Status", "")
        started_at = state.get("StartedAt", "")

        if status == "running" and started_at:
            # Simple ISO timestamp string parse
            clean_time = started_at[:19].replace("T", " ")
            return f"Up since {clean_time}"
        elif status == "exited":
            exit_code = state.get("ExitCode", 0)
            return f"Exited ({exit_code})"
        elif status == "paused":
            return "Paused"
        return status.capitalize()

    # Container Actions
    def restart_container(self, container_id: str, timeout: int = 10) -> tuple[bool, str]:
        """Restart container."""
        if not self.is_connected or not self.client:
            return False, "Docker daemon not connected"
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            return True, f"Container '{container.name}' restarted successfully"
        except NotFound:
            return False, f"Container {container_id[:12]} not found"
        except APIError as e:
            return False, f"API Error: {e.explanation}"
        except Exception as e:
            return False, f"Error: {e!s}"

    def start_container(self, container_id: str) -> tuple[bool, str]:
        """Start container."""
        if not self.is_connected or not self.client:
            return False, "Docker daemon not connected"
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return True, f"Container '{container.name}' started"
        except Exception as e:
            return False, f"Failed to start: {e!s}"

    def stop_container(self, container_id: str, timeout: int = 10) -> tuple[bool, str]:
        """Stop container."""
        if not self.is_connected or not self.client:
            return False, "Docker daemon not connected"
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            return True, f"Container '{container.name}' stopped"
        except Exception as e:
            return False, f"Failed to stop: {e!s}"

    def pause_container(self, container_id: str) -> tuple[bool, str]:
        """Pause or unpause container depending on current state."""
        if not self.is_connected or not self.client:
            return False, "Docker daemon not connected"
        try:
            container = self.client.containers.get(container_id)
            if container.status == "paused":
                container.unpause()
                return True, f"Container '{container.name}' unpaused"
            else:
                container.pause()
                return True, f"Container '{container.name}' paused"
        except Exception as e:
            return False, f"Pause/Unpause failed: {e!s}"

    def remove_container(self, container_id: str, force: bool = False) -> tuple[bool, str]:
        """Remove container."""
        if not self.is_connected or not self.client:
            return False, "Docker daemon not connected"
        try:
            container = self.client.containers.get(container_id)
            name = container.name
            container.remove(force=force)
            if container_id in self._cached_stats:
                del self._cached_stats[container_id]
            return True, f"Container '{name}' removed"
        except Exception as e:
            return False, f"Failed to remove container: {e!s}"

    def get_container_logs(
        self,
        container_id: str,
        tail: int = 150,
        timestamps: bool = True
    ) -> tuple[bool, str]:
        """Fetch latest logs from a container."""
        if not self.is_connected or not self.client:
            return False, "Docker daemon not connected"
        try:
            container = self.client.containers.get(container_id)
            logs_bytes = container.logs(
                stdout=True,
                stderr=True,
                tail=tail,
                timestamps=timestamps
            )
            logs_text = logs_bytes.decode("utf-8", errors="replace")
            return True, logs_text
        except Exception as e:
            return False, f"Error fetching logs: {e!s}"
