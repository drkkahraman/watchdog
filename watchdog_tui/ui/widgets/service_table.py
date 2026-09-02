"""Reverse Proxy and Port Forwardings View."""


from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import DataTable, Input, Static

from watchdog_tui.models import ProxyRoute


class ServiceTableWidget(Container):
    """DataTable displaying exposed ports, host mappings, and reverse proxy routes."""

    DEFAULT_CSS = """
    ServiceTableWidget {
        height: 1fr;
        layout: vertical;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.routes: list[ProxyRoute] = []
        self.filter_query: str = ""

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-container"):
            yield Input(placeholder="🔍 Filter routes, domains, ports, or containers...", id="service-search-input")
            yield Static("0 routes detected", id="service-status-label")

        yield DataTable(id="services-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#services-table", DataTable)
        table.add_columns(
            "TYPE",
            "CONTAINER",
            "ENTRYPOINT / HOST",
            "RULE / DOMAIN",
            "TARGET PORT",
            "TLS/SSL",
            "DETAILS",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "service-search-input":
            self.filter_query = event.value.strip().lower()
            self.refresh_table()

    def set_routes(self, routes: list[ProxyRoute]) -> None:
        """Update proxy routes and refresh table."""
        self.routes = routes
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one("#services-table", DataTable)
        label = self.query_one("#service-status-label", Static)

        filtered = [
            r for r in self.routes
            if not self.filter_query
            or self.filter_query in r.container_name.lower()
            or self.filter_query in r.service_type.lower()
            or self.filter_query in r.rule_or_domain.lower()
            or self.filter_query in r.target_port.lower()
            or self.filter_query in r.entrypoint_or_host.lower()
        ]

        label.update(f"{len(filtered)}/{len(self.routes)} routes/ports")
        table.clear()

        for r in filtered:
            # Service type styling
            type_style = "bold magenta" if "Traefik" in r.service_type else (
                "bold green" if "Caddy" in r.service_type else (
                    "bold cyan" if "Nginx" in r.service_type else "bold yellow"
                )
            )
            type_text = Text(r.service_type, style=type_style)
            container_text = Text(r.container_name, style="bold white")
            host_text = Text(r.entrypoint_or_host, style="cyan")
            domain_text = Text(r.rule_or_domain, style="bold bright_white")
            target_text = Text(r.target_port, style="yellow")
            tls_text = Text("🔒 YES" if r.tls_enabled else "🔓 NO", style="green" if r.tls_enabled else "dim")
            details_text = Text(r.details or "-", style="dim")

            table.add_row(
                type_text,
                container_text,
                host_text,
                domain_text,
                target_text,
                tls_text,
                details_text,
            )
