from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Static
from textual.widget import Widget


class RunRequested(Message):
    bubble = True


class TopBar(Widget):
    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Button("Run", id="run", variant="primary")
            yield Static("", id="topbar-info")

    def set_info(self, text: str) -> None:
        self.query_one("#topbar-info", Static).update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            self.post_message(RunRequested())
