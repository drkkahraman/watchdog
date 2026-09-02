"""Help and Keybinding Cheatsheet Modal."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Static


class HelpModal(ModalScreen):
    """Modal displaying full keyboard shortcuts and documentation."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("?", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="help-dialog"):
            yield Static("🐕 Watchdog Keyboard Shortcuts & Quick Guide", classes="modal-title")
            yield DataTable(id="help-table", cursor_type="none")
            yield Button("Close (Esc/?)", id="btn-close", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#help-table", DataTable)
        table.add_columns("KEY", "ACTION", "DESCRIPTION")

        shortcuts = [
            ("r", "Restart Container", "Trigger container restart with a 10s grace period"),
            ("s", "Start / Stop", "Toggle start or stop state of the selected container"),
            ("p", "Pause / Unpause", "Suspend or resume container execution processes"),
            ("l", "View Logs", "Open real-time streaming log viewer with tail & filter"),
            ("i", "Inspect Details", "Open full container metadata, env vars, networks & JSON"),
            ("x / d", "Remove Container", "Safely delete container with confirmation prompt"),
            ("f / /", "Filter Containers", "Quick jump to container search bar"),
            ("1", "Containers View", "Switch to main Containers dashboard"),
            ("2", "Services View", "Switch to Reverse Proxy & Port mappings"),
            ("space", "Pause/Resume in Logs", "Toggles live log tail streaming"),
            ("?", "Help Modal", "Show this cheatsheet dialog"),
            ("q / Ctrl+C", "Quit Watchdog", "Exit cleanly to terminal shell"),
        ]

        for key, action, desc in shortcuts:
            table.add_row(f"[bold cyan]{key}[/bold cyan]", f"[bold yellow]{action}[/bold yellow]", desc)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.action_close()

    def action_close(self) -> None:
        self.dismiss()
