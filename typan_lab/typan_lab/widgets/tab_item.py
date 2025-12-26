from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Label


@dataclass(frozen=True)
class TabItemModel:
    path: Path
    active: bool
    dirty: bool
    key: str


class TabItem(Horizontal):
    def __init__(self, model: TabItemModel) -> None:
        classes = "tab" + (" is-active" if model.active else "")
        super().__init__(classes=classes)
        self.model = model

    def compose(self) -> ComposeResult:
        yield Label("★" if self.model.dirty else " ", classes="tab-star")
        yield Button(self.model.path.name, id=f"tab_{self.model.key}", classes="tab-title")
        yield Button("×", id=f"close_{self.model.key}", classes="tab-close")
