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
            ("s", "Start / Stop (Toggle)", "Durdur veya başlat (duruma göre otomatik geçiş)"),
            ("a", "Start Container", "Seçili container'ı doğrudan başlatır (▶ Start)"),
            ("t", "Stop Container", "Seçili container'ı onay ile durdurur (⏹ Stop)"),
            ("k", "Force Kill", "Container'ı beklemeden anında zorla kapatır (SIGKILL)"),
            ("r", "Restart Container", "Container'ı zarifçe yeniden başlatır (↻ Restart)"),
            ("x / d / Del", "Delete (Sil)", "Container'ı onay ekranıyla kalıcı olarak siler (🗑️)"),
            ("p", "Pause / Unpause", "Container süreçlerini askıya alır / devam ettirir"),
            ("l / Enter", "View Logs", "Canlı akan log izleme ekranını açar (Filtreli & Tail)"),
            ("i", "Inspect Details", "Container IP, Port, Mount, Env ve ham JSON detayları"),
            ("f / /", "Filter Containers", "İsme, duruma veya porta göre canlı arama"),
            ("1 / 2", "Switch Tabs", "Containers ve Reverse Proxy/Ports sekmeleri arası geçiş"),
            ("?", "Help Modal", "Bu kısayol yardım ekranını açar"),
            ("q / Ctrl+C", "Quit Watchdog", "Uygulamadan temiz bir şekilde çıkar"),
        ]

        for key, action, desc in shortcuts:
            table.add_row(f"[bold cyan]{key}[/bold cyan]", f"[bold yellow]{action}[/bold yellow]", desc)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.action_close()

    def action_close(self) -> None:
        self.dismiss()
