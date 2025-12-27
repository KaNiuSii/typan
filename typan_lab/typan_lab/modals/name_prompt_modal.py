from __future__ import annotations

from dataclasses import dataclass
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


@dataclass(frozen=True)
class NamePromptResult:
    name: str


class NamePromptModal(ModalScreen[NamePromptResult | None]):
    """Modal that asks for a single name. Dismisses with NamePromptResult or None."""

    def __init__(self, title: str, placeholder: str = "name", initial: str = "") -> None:
        super().__init__()
        self._title = title
        self._placeholder = placeholder
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Vertical(id="np-root"):
            yield Label(self._title, id="np-title")
            yield Input(value=self._initial, placeholder=self._placeholder, id="np-input")

            with Horizontal(id="np-buttons"):
                yield Button("Cancel", id="np-cancel", variant="default")
                yield Button("OK", id="np-ok", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#np-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "np-cancel":
            self.dismiss(None)
            return

        if event.button.id == "np-ok":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "np-input":
            self._submit()

    def _submit(self) -> None:
        value = self.query_one("#np-input", Input).value.strip()
        if not value:
            # keep modal open, just ignore empty
            return
        self.dismiss(NamePromptResult(name=value))
