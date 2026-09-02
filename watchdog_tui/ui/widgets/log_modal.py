"""Real-time Container Log Viewer Modal."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, RichLog, Static

from watchdog_tui.core.docker_manager import DockerManager
from watchdog_tui.models import ContainerInfo


class LogModal(ModalScreen):
    """Modal screen displaying live container logs."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("r", "refresh_logs", "Refresh"),
    ]

    def __init__(self, docker_manager: DockerManager, container: ContainerInfo) -> None:
        super().__init__()
        self.docker_manager = docker_manager
        self.container = container
        self.is_paused: bool = False
        self.tail_count: int = 150
        self.filter_query: str = ""
        self.all_logs: str = ""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(
                f"📋 Logs: {self.container.name} ({self.container.short_id})",
                classes="modal-title"
            )

            with Horizontal(id="search-container"):
                yield Input(placeholder="🔍 Filter log output (regex / text)...", id="log-search-input")
                yield Static(f"Tail: {self.tail_count} lines", id="log-tail-label")

            yield RichLog(id="log-text-area", highlight=True, markup=True, wrap=True)

            with Horizontal(id="log-controls"):
                yield Button("Pause Stream (Space)", id="btn-pause", classes="log-btn")
                yield Button("Tail 100", id="btn-tail-100", classes="log-btn")
                yield Button("Tail 500", id="btn-tail-500", classes="log-btn")
                yield Button("Tail 1000", id="btn-tail-1000", classes="log-btn")
                yield Button("Refresh (R)", id="btn-refresh", classes="log-btn")
                yield Button("Close (Esc/Q)", id="btn-close", variant="error", classes="log-btn")

    def on_mount(self) -> None:
        self.refresh_logs()
        # Set periodic log refresh timer
        self.set_interval(2.0, self._auto_refresh)

    def _auto_refresh(self) -> None:
        if not self.is_paused:
            self.refresh_logs()

    def refresh_logs(self) -> None:
        """Fetch and render logs."""
        success, logs = self.docker_manager.get_container_logs(
            self.container.id,
            tail=self.tail_count,
            timestamps=True
        )
        if success:
            self.all_logs = logs
            self._render_logs()
        else:
            log_view = self.query_one("#log-text-area", RichLog)
            log_view.clear()
            log_view.write(f"[bold red]Failed to fetch logs: {logs}[/bold red]")

    def _render_logs(self) -> None:
        log_view = self.query_one("#log-text-area", RichLog)
        log_view.clear()

        lines = self.all_logs.splitlines()
        if self.filter_query:
            lines = [line for line in lines if self.filter_query.lower() in line.lower()]

        if not lines:
            log_view.write("[dim]-- No log entries found --[/dim]")
            return

        for line in lines:
            # Highlight error/warning keywords
            formatted_line = line
            if "ERROR" in line or "error" in line or "FATAL" in line or "Exception" in line:
                formatted_line = f"[red]{line}[/red]"
            elif "WARN" in line or "warning" in line:
                formatted_line = f"[yellow]{line}[/yellow]"
            elif "INFO" in line:
                formatted_line = f"[white]{line}[/white]"
            else:
                formatted_line = f"[bright_black]{line}[/bright_black]"

            log_view.write(formatted_line)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "log-search-input":
            self.filter_query = event.value.strip()
            self._render_logs()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-close":
            self.action_close()
        elif btn_id == "btn-pause":
            self.action_toggle_pause()
        elif btn_id == "btn-refresh":
            self.refresh_logs()
        elif btn_id == "btn-tail-100":
            self.tail_count = 100
            self.query_one("#log-tail-label", Static).update("Tail: 100 lines")
            self.refresh_logs()
        elif btn_id == "btn-tail-500":
            self.tail_count = 500
            self.query_one("#log-tail-label", Static).update("Tail: 500 lines")
            self.refresh_logs()
        elif btn_id == "btn-tail-1000":
            self.tail_count = 1000
            self.query_one("#log-tail-label", Static).update("Tail: 1000 lines")
            self.refresh_logs()

    def action_toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
        btn = self.query_one("#btn-pause", Button)
        if self.is_paused:
            btn.label = "Resume Stream (Space)"
            btn.variant = "warning"
        else:
            btn.label = "Pause Stream (Space)"
            btn.variant = "default"

    def action_refresh_logs(self) -> None:
        self.refresh_logs()

    def action_close(self) -> None:
        self.dismiss()
