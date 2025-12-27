from __future__ import annotations

from dataclasses import dataclass
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


@dataclass(frozen=True)
class ConfirmResult:
    confirmed: bool


class ConfirmModal(ModalScreen[ConfirmResult]):
    """Yes/No confirmation modal."""

    def __init__(self, title: str, message: str, yes_text: str = "Yes", no_text: str = "No") -> None:
        super().__init__()
        self._title = title
        self._message = message
        self._yes_text = yes_text
        self._no_text = no_text

    def compose(self) -> ComposeResult:
        with Vertical(id="cf-root"):
            yield Label(self._title, id="cf-title")
            yield Label(self._message, id="cf-message")

            with Horizontal(id="cf-buttons"):
                yield Button(self._no_text, id="cf-no", variant="default")
                yield Button(self._yes_text, id="cf-yes", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cf-yes":
            self.dismiss(ConfirmResult(confirmed=True))
        else:
            self.dismiss(ConfirmResult(confirmed=False))
