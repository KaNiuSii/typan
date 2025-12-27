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
        yield TextArea.code_editor("", id="editor-text", language="python")

    def set_active_file(self, path: Path | None) -> None:
        self.active_file = path

    def set_text(self, text: str) -> None:
        editor = self.query_one("#editor-text", TextArea)

        # --- capture state ---
        try:
            cursor = editor.cursor_location  # (row, col)
        except Exception:
            cursor = (0, 0)

        try:
            scroll_y = editor.scroll_y
            scroll_x = editor.scroll_x
        except Exception:
            scroll_y, scroll_x = 0, 0

        self._suspend_change_event = True
        editor.load_text(text)
        self._suspend_change_event = False

        # --- restore state (clamp) ---
        try:
            # clamp row
            lines = text.splitlines() or [""]
            row = max(0, min(cursor[0], len(lines) - 1))
            col = max(0, min(cursor[1], len(lines[row])))

            editor.cursor_location = (row, col)
            editor.scroll_to(scroll_y, scroll_x, animate=False)
        except Exception:
            pass

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if self._suspend_change_event:
            return
        if self.active_file is None:
            return
        self.post_message(BufferEdited(self.active_file, event.text_area.text))
