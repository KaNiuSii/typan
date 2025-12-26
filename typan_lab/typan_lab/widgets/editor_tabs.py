from __future__ import annotations

import hashlib
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.message import Message
from textual.widgets import Button, Label, TextArea

from typan_lab.widgets.tab_item import TabItem, TabItemModel


class BufferEdited(Message):
    def __init__(self, path: Path, text: str) -> None:
        super().__init__()
        self.path = path
        self.text = text

class TabClosed(Message):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

class ActiveTabRequested(Message):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

class EditorTabs(Widget):

    open_files: list[Path] = reactive(list)
    active_file: Path | None = reactive(None)
    dirty_by_file: dict[Path, bool] = reactive(dict)

    def __init__(self, *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        self._render_gen = 0
        self._btn_to_path: dict[str, Path] = {}
        self._text_by_file: dict[Path, str] = {}
        self._suspend_change_event = False

    def clear(self) -> None:
        self.open_files = []
        self.active_file = None
        self._sync_ui()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="tabs"):
                yield Label("No file open", id="tabs-empty")
            yield TextArea("", id="editor-text")

    def set_buffer(self, path: Path, text: str) -> None:
        self._text_by_file[path] = text
        if path not in self.open_files:
            self.open_files = [*self.open_files, path]
        self.active_file = path
        self._sync_ui()

    def update_buffer_text(self, path: Path, text: str) -> None:
        self._text_by_file[path] = text
        if path == self.active_file:
            self._sync_editor_text(text)

    def _sync_ui(self) -> None:
        self._render_tabs()
        if self.active_file is None:
            self._sync_editor_text("")
        else:
            self._sync_editor_text(self._text_by_file.get(self.active_file, ""))

    def _render_tabs(self) -> None:
        tabs = self.query_one("#tabs", Horizontal)

        for child in list(tabs.children):
            child.remove()

        self._btn_to_path.clear()
        self._render_gen += 1
        gen = self._render_gen

        if not self.open_files:
            tabs.mount(Label("No file open", id=f"tabs_empty_{gen}"))
            return

        for path in self.open_files:
            key = hashlib.sha1(path.as_posix().encode("utf-8")).hexdigest()[:12]
            tab_key = f"{key}_{gen}"

            self._btn_to_path[f"tab_{tab_key}"] = path
            self._btn_to_path[f"close_{tab_key}"] = path

            dirty = bool(self.dirty_by_file.get(path, False))  # <- dodaj to reactive niżej
            active = (path == self.active_file)

            tabs.mount(TabItem(TabItemModel(path=path, active=active, dirty=dirty, key=tab_key)))

    def _sync_editor_text(self, text: str) -> None:
        editor = self.query_one("#editor-text", TextArea)
        self._suspend_change_event = True
        editor.load_text(text)
        self._suspend_change_event = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        path = self._btn_to_path.get(bid)
        if path is None:
            return

        if bid.startswith("tab_"):
            self.post_message(ActiveTabRequested(path))
        elif bid.startswith("close_"):
            self.post_message(TabClosed(path))

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if self._suspend_change_event:
            return
        if self.active_file is None:
            return
        self._text_by_file[self.active_file] = event.text_area.text
        self.post_message(BufferEdited(self.active_file, event.text_area.text))
