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
            ("s", "Start / Stop (Toggle)", "Start stopped container or prompt confirmation to stop"),
            ("a", "Start Container", "Directly start the selected container"),
            ("t", "Stop Container", "Safely stop container with confirmation prompt"),
            ("k", "Force Kill", "Forcefully terminate container immediately (SIGKILL)"),
            ("r", "Restart Container", "Gracefully restart container with a 10s timeout"),
            ("x / d / Del", "Delete Container", "Permanently remove container with confirmation"),
            ("p", "Pause / Unpause", "Suspend or resume container execution processes"),
            ("l / Enter", "View Logs", "Open real-time streaming log viewer with tail & filter"),
            ("i", "Inspect Details", "View environment variables, mounts, networks & raw JSON"),
            ("f / /", "Filter Containers", "Search containers by name, image, status, or port"),
            ("1 / 2", "Switch Tabs", "Switch between Containers view and Reverse Proxy matrix"),
            ("?", "Help Modal", "Show this shortcuts and reference guide"),
            ("q / Ctrl+C", "Quit Watchdog", "Cleanly exit Watchdog and return to shell"),
        ]

        for key, action, desc in shortcuts:
            table.add_row(f"[bold cyan]{key}[/bold cyan]", f"[bold yellow]{action}[/bold yellow]", desc)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.action_close()

    def action_close(self) -> None:
        self.dismiss()
