"""Header overview statistics widget."""

import humanize
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal
from textual.widgets import Static

from watchdog.models import SystemStats


class HeaderStatsWidget(Container):
    """Header displaying Host & Docker telemetry."""

    DEFAULT_CSS = """
    HeaderStatsWidget {
        height: auto;
        dock: top;
        background: #1e293b;
        border-bottom: solid #334155;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="brand-bar"):
            yield Static("🐕 WATCHDOG v0.1.0", id="brand-title")
            yield Static("Docker: Connecting...", id="brand-docker-status")

        with Grid(id="stats-grid"):
            # CPU
            with Container(classes="stat-card", id="card-cpu"):
                yield Static("HOST CPU", classes="stat-card-title")
                yield Static("0.0%", classes="stat-card-value", id="val-cpu")
                yield Static("Cores: -", classes="stat-card-sub", id="sub-cpu")

            # Memory
            with Container(classes="stat-card", id="card-mem"):
                yield Static("HOST MEMORY", classes="stat-card-title")
                yield Static("0.0%", classes="stat-card-value", id="val-mem")
                yield Static("0 / 0 GB", classes="stat-card-sub", id="sub-mem")

            # Disk
            with Container(classes="stat-card", id="card-disk"):
                yield Static("HOST DISK", classes="stat-card-title")
                yield Static("0.0%", classes="stat-card-value", id="val-disk")
                yield Static("0 / 0 GB", classes="stat-card-sub", id="sub-disk")

            # Network
            with Container(classes="stat-card", id="card-net"):
                yield Static("HOST NETWORK", classes="stat-card-title")
                yield Static("▲ 0 B/s", classes="stat-card-value", id="val-net")
                yield Static("▼ 0 B/s", classes="stat-card-sub", id="sub-net")

            # Docker stats
            with Container(classes="stat-card", id="card-docker"):
                yield Static("CONTAINERS", classes="stat-card-title")
                yield Static("0 Running", classes="stat-card-value", id="val-docker")
                yield Static("0 Total / 0 Img", classes="stat-card-sub", id="sub-docker")

    def update_stats(self, stats: SystemStats, docker_info: dict) -> None:
        """Update widget with latest system and docker telemetry."""
        # Docker status bar
        docker_status_widget = self.query_one("#brand-docker-status", Static)
        if docker_info.get("connected"):
            v = docker_info.get("version", "")
            os_name = docker_info.get("os", "Linux")
            docker_status_widget.update(
                Text.assemble(
                    ("● DOCKER CONNECTED ", "bold green"),
                    (f"| Engine: v{v} ({os_name})", "dim")
                )
            )
        else:
            err = docker_info.get("error", "Not reachable")
            docker_status_widget.update(
                Text.assemble(
                    ("● DOCKER DISCONNECTED ", "bold red"),
                    (f"| {err}", "italic red")
                )
            )

        # CPU
        cpu_val = self.query_one("#val-cpu", Static)
        cpu_sub = self.query_one("#sub-cpu", Static)
        cpu_color = "green" if stats.cpu_percent < 60 else "yellow" if stats.cpu_percent < 85 else "red"
        cpu_val.update(Text(f"{stats.cpu_percent:.1f}%", style=f"bold {cpu_color}"))
        freq_str = f" @ {stats.cpu_freq_mhz:.0f}MHz" if stats.cpu_freq_mhz > 0 else ""
        cpu_sub.update(f"{stats.cpu_count} Cores{freq_str}")

        # Memory
        mem_val = self.query_one("#val-mem", Static)
        mem_sub = self.query_one("#sub-mem", Static)
        mem_color = "green" if stats.memory_percent < 70 else "yellow" if stats.memory_percent < 88 else "red"
        mem_val.update(Text(f"{stats.memory_percent:.1f}%", style=f"bold {mem_color}"))
        used_str = humanize.naturalsize(stats.memory_used, binary=True)
        total_str = humanize.naturalsize(stats.memory_total, binary=True)
        mem_sub.update(f"{used_str} / {total_str}")

        # Disk
        disk_val = self.query_one("#val-disk", Static)
        disk_sub = self.query_one("#sub-disk", Static)
        disk_color = "green" if stats.disk_percent < 75 else "yellow" if stats.disk_percent < 90 else "red"
        disk_val.update(Text(f"{stats.disk_percent:.1f}%", style=f"bold {disk_color}"))
        d_used = humanize.naturalsize(stats.disk_used, binary=True)
        d_total = humanize.naturalsize(stats.disk_total, binary=True)
        disk_sub.update(f"{d_used} / {d_total}")

        # Network
        net_val = self.query_one("#val-net", Static)
        net_sub = self.query_one("#sub-net", Static)
        sent_str = humanize.naturalsize(stats.net_sent_speed)
        recv_str = humanize.naturalsize(stats.net_recv_speed)
        net_val.update(Text(f"▲ {sent_str}/s", style="cyan"))
        net_sub.update(Text(f"▼ {recv_str}/s", style="blue"))

        # Docker Summary
        doc_val = self.query_one("#val-docker", Static)
        doc_sub = self.query_one("#sub-docker", Static)
        running = docker_info.get("containers_running", 0)
        total = docker_info.get("containers_total", 0)
        paused = docker_info.get("containers_paused", 0)
        images = docker_info.get("images_count", 0)

        doc_val.update(Text(f"{running} Running", style="bold green" if running > 0 else "bold white"))
        extra_str = f" ({paused} p)" if paused > 0 else ""
        doc_sub.update(f"{total} Total{extra_str} | {images} Imgs")
