from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget

from .tab_bar import TabBar
from .editor_pane import EditorPane


class EditorPanel(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield TabBar(id="tabbar")
            yield EditorPane(id="pane")

    def set_tabs(self, open_files: list[Path], active_file: Path | None, dirty_by_file: dict[Path, bool]) -> None:
        self.query_one(TabBar).set_tabs(open_files, active_file, dirty_by_file)

    def set_editor(self, active_file: Path | None, text: str) -> None:
        pane = self.query_one(EditorPane)
        pane.set_active_file(active_file)
        pane.set_text(text)
