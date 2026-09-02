"""Container JSON and Configuration Inspector Modal."""

import json

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, RichLog, Static, TabbedContent, TabPane

from watchdog_tui.models import ContainerInfo


class InspectModal(ModalScreen):
    """Modal screen displaying detailed inspection attributes."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
    ]

    def __init__(self, container: ContainerInfo) -> None:
        super().__init__()
        self.container = container

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(
                f"🔍 Inspect: {self.container.name} ({self.container.short_id})",
                classes="modal-title"
            )

            with TabbedContent():
                # Overview Tab
                with TabPane("Overview"):
                    yield RichLog(id="inspect-overview-log", highlight=True, markup=True)

                # Environment Variables Tab
                with TabPane("Environment"):
                    yield RichLog(id="inspect-env-log", highlight=True, markup=True)

                # Networks & Ports Tab
                with TabPane("Network & Ports"):
                    yield RichLog(id="inspect-net-log", highlight=True, markup=True)

                # Mounts / Volumes Tab
                with TabPane("Mounts & Volumes"):
                    yield RichLog(id="inspect-mounts-log", highlight=True, markup=True)

                # Raw JSON Tab
                with TabPane("Raw JSON"):
                    yield RichLog(id="inspect-raw-log", highlight=True, markup=True)

            with Horizontal(id="log-controls"):
                yield Button("Close (Esc/Q)", id="btn-close", variant="primary", classes="log-btn")

    def on_mount(self) -> None:
        raw = self.container.raw_data or {}
        config = raw.get("Config", {})
        state = raw.get("State", {})
        net_settings = raw.get("NetworkSettings", {})
        mounts = raw.get("Mounts", [])

        # 1. Overview
        overview_log = self.query_one("#inspect-overview-log", RichLog)
        overview_log.write(f"[bold cyan]Container ID:[/bold cyan] {self.container.id}")
        overview_log.write(f"[bold cyan]Name:[/bold cyan] {self.container.name}")
        overview_log.write(f"[bold cyan]Image:[/bold cyan] {self.container.image}")
        overview_log.write(f"[bold cyan]Status:[/bold cyan] {self.container.status} ({self.container.health or 'no healthcheck'})")
        overview_log.write(f"[bold cyan]Created:[/bold cyan] {self.container.created_at}")
        overview_log.write(f"[bold cyan]Started At:[/bold cyan] {state.get('StartedAt', 'N/A')}")
        overview_log.write(f"[bold cyan]Finished At:[/bold cyan] {state.get('FinishedAt', 'N/A')}")
        overview_log.write(f"[bold cyan]Restart Count:[/bold cyan] {raw.get('RestartCount', 0)}")
        overview_log.write(f"[bold cyan]Platform:[/bold cyan] {raw.get('Platform', 'linux')}")
        overview_log.write(f"[bold cyan]Driver:[/bold cyan] {raw.get('Driver', 'N/A')}")
        overview_log.write(f"[bold cyan]Cmd:[/bold cyan] {' '.join(config.get('Cmd') or [])}")
        overview_log.write(f"[bold cyan]Entrypoint:[/bold cyan] {' '.join(config.get('Entrypoint') or [])}")
        overview_log.write(f"[bold cyan]WorkingDir:[/bold cyan] {config.get('WorkingDir') or '/'}")

        # 2. Environment
        env_log = self.query_one("#inspect-env-log", RichLog)
        env_vars = config.get("Env", [])
        if env_vars:
            for env in sorted(env_vars):
                if "=" in env:
                    k, v = env.split("=", 1)
                    # Hide password values slightly for safety
                    if any(secret in k.lower() for secret in ("pass", "secret", "token", "key")):
                        v_disp = v[:3] + "********" if len(v) > 3 else "********"
                    else:
                        v_disp = v
                    env_log.write(f"[bold green]{k}[/bold green] = [white]{v_disp}[/white]")
                else:
                    env_log.write(f"[white]{env}[/white]")
        else:
            env_log.write("[dim]No environment variables defined.[/dim]")

        # 3. Network & Ports
        net_log = self.query_one("#inspect-net-log", RichLog)
        networks = net_settings.get("Networks", {})
        net_log.write("[bold cyan]Connected Networks:[/bold cyan]")
        for net_name, net_data in networks.items():
            net_log.write(f"  • [bold yellow]{net_name}[/bold yellow] (IP: {net_data.get('IPAddress')}, Gateway: {net_data.get('Gateway')}, Mac: {net_data.get('MacAddress')})")

        net_log.write("\n[bold cyan]Port Bindings:[/bold cyan]")
        if self.container.ports:
            for p in self.container.ports:
                net_log.write(f"  • {p}")
        else:
            net_log.write("  [dim]No exposed or bound ports[/dim]")

        # 4. Mounts
        mounts_log = self.query_one("#inspect-mounts-log", RichLog)
        if mounts:
            for m in mounts:
                m_type = m.get("Type", "bind")
                src = m.get("Source", "")
                dst = m.get("Destination", "")
                mode = m.get("Mode", "rw")
                mounts_log.write(f"  • [[bold magenta]{m_type.upper()}[/bold magenta]] [cyan]{src}[/cyan] ➜ [yellow]{dst}[/yellow] ([dim]{mode}[/dim])")
        else:
            mounts_log.write("[dim]No mounts or volumes attached.[/dim]")

        # 5. Raw JSON
        raw_log = self.query_one("#inspect-raw-log", RichLog)
        formatted_json = json.dumps(raw, indent=2)
        raw_log.write(formatted_json)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.action_close()

    def action_close(self) -> None:
        self.dismiss()
