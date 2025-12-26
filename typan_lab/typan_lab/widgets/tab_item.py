from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Label


# ----------------------------
# Model
# ----------------------------

@dataclass(frozen=True)
class TabItemModel:
    """Pure view model for a single editor tab."""
    path: Path
    active: bool
    dirty: bool
    key: str


# ----------------------------
# Widget
# ----------------------------

class TabItem(Horizontal):
    """Single tab in the editor tab bar.

    Stateless widget:
    - receives all state via TabItemModel
    - emits no events on its own (handled by parent via button ids)
    """

    _STAR_CLEAN = " "
    _STAR_DIRTY = "✷"

    def __init__(self, model: TabItemModel) -> None:
        self.model = model
        super().__init__(classes=self._compute_classes(model))

    def compose(self) -> ComposeResult:
        yield Label(
            self._STAR_DIRTY if self.model.dirty else self._STAR_CLEAN,
            classes="tab-star",
        )

        yield Button(
            self.model.path.name,
            id=self._tab_button_id(),
            classes="tab-title",
        )

        yield Button(
            "×",
            id=self._close_button_id(),
            classes="tab-close",
        )

    # ----------------------------
    # Helpers
    # ----------------------------

    @staticmethod
    def _compute_classes(model: TabItemModel) -> str:
        return "tab is-active" if model.active else "tab"

    def _tab_button_id(self) -> str:
        return f"tab_{self.model.key}"

    def _close_button_id(self) -> str:
        return f"close_{self.model.key}"
