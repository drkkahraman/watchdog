"""Safe Confirmation Dialog for Destructive Actions."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmModal(ModalScreen[bool]):
    """Modal confirmation dialog for stopping, killing, or removing containers."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("n", "cancel", "Cancel"),
        Binding("y", "confirm", "Confirm"),
    ]

    def __init__(
        self,
        title: str,
        message: str,
        action_label: str = "Confirm",
        is_danger: bool = True
    ) -> None:
        super().__init__()
        self.modal_title = title
        self.message = message
        self.action_label = action_label
        self.is_danger = is_danger

    def compose(self) -> ComposeResult:
        with Vertical(classes="confirm-dialog"):
            yield Static(self.modal_title, classes="modal-title")
            yield Static(self.message, id="confirm-message")

            with Horizontal(id="confirm-buttons"):
                variant = "error" if self.is_danger else "primary"
                yield Button(f"{self.action_label} (Y)", id="btn-confirm", variant=variant, classes="btn-danger")
                yield Button("Cancel (Esc/N)", id="btn-cancel", variant="default", classes="btn-secondary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        elif event.button.id == "btn-cancel":
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
