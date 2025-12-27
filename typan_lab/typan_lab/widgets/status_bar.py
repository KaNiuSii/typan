from __future__ import annotations
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label
from textual.reactive import reactive

class StatusBar(Widget):
    active_file: Path | None = reactive(None)
    dirty: bool = reactive(False)

    def compose(self) -> ComposeResult:
        yield Label("", id="status")

    def watch_active_file(self, _: object) -> None:
        self._render()

    def watch_dirty(self, _: object) -> None:
        self._render()

    def _render(self) -> None:
        label = self.query_one("#status", Label)
        if self.active_file is None:
            label.update("No file")
        else:
            star = " *" if self.dirty else ""
            label.update(f"{self.active_file}{star}")
