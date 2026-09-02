"""Interactive Container List and Detail Table."""


import humanize
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Input, Static

from watchdog_tui.models import ContainerInfo


class ContainerTableWidget(Container):
    """Main container data table with search and quick details."""

    DEFAULT_CSS = """
    ContainerTableWidget {
        height: 1fr;
        layout: vertical;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.containers: list[ContainerInfo] = []
        self.filter_query: str = ""
        self.selected_container_id: str | None = None
        self._row_keys: dict[str, str] = {}  # container_id -> row_key

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-container"):
            yield Input(placeholder="🔍 Type / or press 'f' to filter containers (name, image, status)...", id="container-search-input")
            yield Static("0 containers", id="filter-status-label")

        yield DataTable(id="containers-table", cursor_type="row", zebra_stripes=True)

        with Horizontal(id="quick-details-pane"):
            with Vertical(id="quick-details-left"):
                yield Static("Select a container to view details", id="detail-line-1", classes="detail-line")
                yield Static("", id="detail-line-2", classes="detail-line")
                yield Static("", id="detail-line-3", classes="detail-line")
            with Vertical(id="quick-details-right"):
                yield Static("", id="detail-line-4", classes="detail-line")
                yield Static("", id="detail-line-5", classes="detail-line")
                yield Static("", id="detail-line-6", classes="detail-line")

    def on_mount(self) -> None:
        table = self.query_one("#containers-table", DataTable)
        table.add_columns(
            "STATUS",
            "NAME",
            "ID",
            "IMAGE",
            "CPU %",
            "MEMORY",
            "NET I/O",
            "BLOCK I/O",
            "PORTS",
            "UPTIME",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "container-search-input":
            self.filter_query = event.value.strip().lower()
            self.refresh_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._update_selected_from_cursor()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self._update_selected_from_cursor()

    def _update_selected_from_cursor(self) -> None:
        table = self.query_one("#containers-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._get_filtered_containers()):
            filtered = self._get_filtered_containers()
            selected = filtered[table.cursor_row]
            self.selected_container_id = selected.id
            self._update_details_pane(selected)

    def get_selected_container(self) -> ContainerInfo | None:
        """Get the currently highlighted container."""
        if not self.selected_container_id:
            filtered = self._get_filtered_containers()
            if filtered:
                return filtered[0]
            return None

        for c in self.containers:
            if c.id == self.selected_container_id or c.short_id == self.selected_container_id:
                return c

        filtered = self._get_filtered_containers()
        return filtered[0] if filtered else None

    def _get_filtered_containers(self) -> list[ContainerInfo]:
        if not self.filter_query:
            return self.containers
        return [
            c for c in self.containers
            if (
                self.filter_query in c.name.lower()
                or self.filter_query in c.image.lower()
                or self.filter_query in c.status.lower()
                or self.filter_query in c.short_id.lower()
                or (c.health and self.filter_query in c.health.lower())
            )
        ]

    def set_containers(self, containers: list[ContainerInfo]) -> None:
        """Update container list and refresh UI."""
        self.containers = containers
        self.refresh_table()

    def refresh_table(self) -> None:
        """Render container rows in data table."""
        table = self.query_one("#containers-table", DataTable)
        label = self.query_one("#filter-status-label", Static)
        filtered = self._get_filtered_containers()

        total = len(self.containers)
        showing = len(filtered)
        label.update(f"{showing}/{total} containers")

        # Remember previous cursor position if possible
        prev_cursor = table.cursor_row

        table.clear()

        for c in filtered:
            # Status Badge
            status_text = self._format_status(c)
            name_text = Text(c.name, style="bold white")
            id_text = Text(c.short_id, style="dim cyan")
            img_text = Text(c.image[:32] + "..." if len(c.image) > 35 else c.image, style="bright_black")

            # CPU
            cpu_val = c.stats.cpu_percent
            cpu_style = "green" if cpu_val < 50 else "yellow" if cpu_val < 80 else "red"
            cpu_text = Text(f"{cpu_val:5.1f}%", style=cpu_style)

            # Memory
            if c.stats.memory_limit > 0:
                mem_used_str = humanize.naturalsize(c.stats.memory_usage, binary=True)
                mem_pct = c.stats.memory_percent
                mem_style = "green" if mem_pct < 60 else "yellow" if mem_pct < 85 else "red"
                mem_text = Text(f"{mem_used_str} ({mem_pct:.0f}%)", style=mem_style)
            else:
                mem_text = Text("-", style="dim")

            # Net I/O
            if c.stats.net_rx_bytes > 0 or c.stats.net_tx_bytes > 0:
                rx_str = humanize.naturalsize(c.stats.net_rx_bytes)
                tx_str = humanize.naturalsize(c.stats.net_tx_bytes)
                net_text = Text(f"▼{rx_str} ▲{tx_str}", style="blue")
            else:
                net_text = Text("-", style="dim")

            # Block I/O
            if c.stats.block_read_bytes > 0 or c.stats.block_write_bytes > 0:
                r_str = humanize.naturalsize(c.stats.block_read_bytes)
                w_str = humanize.naturalsize(c.stats.block_write_bytes)
                blk_text = Text(f"R:{r_str} W:{w_str}", style="magenta")
            else:
                blk_text = Text("-", style="dim")

            # Ports
            ports_summary = ", ".join(
                f"{p.host_port}->{p.container_port}" if p.host_port else f"{p.container_port}"
                for p in c.ports[:2]
            )
            if len(c.ports) > 2:
                ports_summary += f" (+{len(c.ports)-2})"
            ports_text = Text(ports_summary or "-", style="yellow" if ports_summary else "dim")

            # Uptime
            uptime_text = Text(c.uptime, style="italic")

            table.add_row(
                status_text,
                name_text,
                id_text,
                img_text,
                cpu_text,
                mem_text,
                net_text,
                blk_text,
                ports_text,
                uptime_text,
                key=c.id
            )

        # Restore cursor
        if filtered:
            if prev_cursor is not None and prev_cursor < len(filtered):
                table.move_cursor(row=prev_cursor)
            else:
                table.move_cursor(row=0)
            self._update_selected_from_cursor()
        else:
            self._clear_details_pane()

    def _format_status(self, c: ContainerInfo) -> Text:
        status = c.status.lower()
        if status == "running":
            health_str = f" ({c.health})" if c.health else ""
            if c.health == "healthy":
                return Text(f"● RUNNING{health_str}", style="bold green")
            elif c.health == "unhealthy":
                return Text(f"● RUNNING{health_str}", style="bold red")
            elif c.health == "starting":
                return Text("● STARTING", style="bold yellow")
            return Text("● RUNNING", style="bold green")
        elif status == "paused":
            return Text("❚❚ PAUSED", style="bold yellow")
        elif status == "restarting":
            return Text("↻ RESTARTING", style="bold cyan")
        elif status == "exited":
            return Text("■ EXITED", style="dim red")
        else:
            return Text(f"○ {status.upper()}", style="dim")

    def _update_details_pane(self, c: ContainerInfo) -> None:
        raw = c.raw_data or {}
        config = raw.get("Config", {})
        net_settings = raw.get("NetworkSettings", {})

        # IP addresses & networks
        networks = list(net_settings.get("Networks", {}).keys())
        ip_addr = net_settings.get("IPAddress") or (
            list(net_settings.get("Networks", {}).values())[0].get("IPAddress")
            if net_settings.get("Networks") else "N/A"
        )

        cmd = " ".join(config.get("Cmd") or []) if config.get("Cmd") else "None"
        if len(cmd) > 60:
            cmd = cmd[:57] + "..."

        mounts = [
            f"{m.get('Source', '')}:{m.get('Destination', '')}"
            for m in raw.get("Mounts", [])[:2]
        ]
        mounts_str = ", ".join(mounts) if mounts else "None"
        if len(mounts_str) > 50:
            mounts_str = mounts_str[:47] + "..."

        self.query_one("#detail-line-1", Static).update(
            Text.assemble(("Container: ", "bold cyan"), (f"{c.name} ", "bold white"), (f"({c.id[:12]})", "dim"))
        )
        self.query_one("#detail-line-2", Static).update(
            Text.assemble(("Command: ", "bold cyan"), (cmd, "white"))
        )
        self.query_one("#detail-line-3", Static).update(
            Text.assemble(("Mounts: ", "bold cyan"), (mounts_str, "white"))
        )
        self.query_one("#detail-line-4", Static).update(
            Text.assemble(("Network: ", "bold cyan"), (f"{', '.join(networks) or 'bridge'} (IP: {ip_addr})", "white"))
        )
        self.query_one("#detail-line-5", Static).update(
            Text.assemble(("PIDs: ", "bold cyan"), (f"{c.stats.pids}", "white"), (" | Created: ", "bold cyan"), (c.created_at[:19].replace("T", " "), "white"))
        )
        self.query_one("#detail-line-6", Static).update(
            Text.assemble(("Shortcuts: ", "bold cyan"), ("[R]estart  [S]top/Start  [P]ause  [L]ogs  [I]nspect  [X]Remove", "yellow"))
        )

    def _clear_details_pane(self) -> None:
        self.query_one("#detail-line-1", Static).update("No container selected")
        self.query_one("#detail-line-2", Static).update("")
        self.query_one("#detail-line-3", Static).update("")
        self.query_one("#detail-line-4", Static).update("")
        self.query_one("#detail-line-5", Static).update("")
        self.query_one("#detail-line-6", Static).update("")
