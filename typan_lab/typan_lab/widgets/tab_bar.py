from __future__ import annotations

import hashlib
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label

from .tab_item import TabItem, TabItemModel


class TabClosed(Message):
    bubble = True
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path


class ActiveTabRequested(Message):
    bubble = True
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path


class TabBar(Widget):
    open_files: list[Path] = reactive(list)
    active_file: Path | None = reactive(None)
    dirty_by_file: dict[Path, bool] = reactive(dict)

    def __init__(self, *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        self._btn_to_path: dict[str, Path] = {}

    def compose(self) -> ComposeResult:
        with Horizontal(id="tabs"):
            yield Label("No file open", id="tabs-empty")

    def set_tabs(self, open_files: list[Path], active_file: Path | None, dirty_by_file: dict[Path, bool]) -> None:
        open_files = list(open_files)
        dirty_by_file = dict(dirty_by_file)

        if self.open_files != open_files:
            self.open_files = open_files
        if self.active_file != active_file:
            self.active_file = active_file
        if self.dirty_by_file != dirty_by_file:
            self.dirty_by_file = dirty_by_file

    def watch_open_files(self, old, new) -> None: self._render_tabs()
    def watch_active_file(self, old, new) -> None: self._render_tabs()
    def watch_dirty_by_file(self, old, new) -> None: self._render_tabs()

    def _render_tabs(self) -> None:
        tabs = self.query_one("#tabs", Horizontal)
        empty = self.query_one("#tabs-empty", Label)

        for child in list(tabs.children):
            if child.id != "tabs-empty":
                child.remove()

        self._btn_to_path.clear()

        if not self.open_files:
            empty.display = True
            return

        empty.display = False

        for path in self.open_files:
            key = self._stable_key(path)
            tab_id = f"tab_{key}"
            close_id = f"close_{key}"

            self._btn_to_path[tab_id] = path
            self._btn_to_path[close_id] = path

            tabs.mount(
                TabItem(
                    TabItemModel(
                        path=path,
                        active=(path == self.active_file),
                        dirty=bool(self.dirty_by_file.get(path, False)),
                        key=key,
                    )
                )
            )

    @staticmethod
    def _stable_key(path: Path) -> str:
        return hashlib.sha1(path.as_posix().encode("utf-8")).hexdigest()[:12]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        path = self._btn_to_path.get(bid)
        if path is None:
            return
        if bid.startswith("tab_"):
            self.post_message(ActiveTabRequested(path))
        elif bid.startswith("close_"):
            self.post_message(TabClosed(path))
