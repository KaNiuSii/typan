from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import TextArea


class BufferEdited(Message):
    bubble = True
    def __init__(self, path: Path, text: str) -> None:
        super().__init__()
        self.path = path
        self.text = text


class EditorPane(Widget):
    active_file: Path | None = reactive(None)

    def __init__(self, *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        self._suspend_change_event = False

    def compose(self) -> ComposeResult:
        yield TextArea("", id="editor-text")

    def set_active_file(self, path: Path | None) -> None:
        self.active_file = path

    def set_text(self, text: str) -> None:
        editor = self.query_one("#editor-text", TextArea)
        self._suspend_change_event = True
        editor.load_text(text)
        self._suspend_change_event = False

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if self._suspend_change_event:
            return
        if self.active_file is None:
            return
        self.post_message(BufferEdited(self.active_file, event.text_area.text))
