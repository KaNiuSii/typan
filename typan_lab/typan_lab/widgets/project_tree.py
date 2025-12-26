from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from textual.widget import Widget
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DirectoryTree

class OpenFileRequested(Message):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

@dataclass
class ProjectTreeConfig:
    root: Path

class ProjectTree(Widget):

    def __init__(self, root: Path, *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        self._root = root

    def compose(self) -> ComposeResult:
        yield DirectoryTree(str(self._root), id="dir-tree")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.post_message(OpenFileRequested(Path(event.path)))
