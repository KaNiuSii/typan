from __future__ import annotations

import hashlib
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, TextArea

from .tab_item import TabItem, TabItemModel


# ----------------------------
# Messages
# ----------------------------

class BufferEdited(Message):
    bubble = True

    def __init__(self, path: Path, text: str) -> None:
        super().__init__()
        self.path = path
        self.text = text


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


# ----------------------------
# Widget
# ----------------------------

class EditorTabs(Widget):
    """Tabs + TextArea editor.

    This widget is a view:
    - receives state from controller via set_tabs() / set_editor_text()
    - emits messages when user interacts
    """

    open_files: list[Path] = reactive(list)
    active_file: Path | None = reactive(None)
    dirty_by_file: dict[Path, bool] = reactive(dict)

    _TABS_SEL = "#tabs"
    _EDITOR_SEL = "#editor-text"

    def __init__(self, *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        self._btn_to_path: dict[str, Path] = {}
        self._suspend_change_event = False

    # --- compose ---

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="tabs"):
                yield Label("No file open", id="tabs-empty")
            yield TextArea("", id="editor-text")

    # --- public API used by screen/controller ---

    def set_tabs(
        self,
        open_files: list[Path],
        active_file: Path | None,
        dirty_by_file: dict[Path, bool],
    ) -> None:
        """Set tabs state. Avoids unnecessary reactive updates."""
        open_files = list(open_files)
        dirty_by_file = dict(dirty_by_file)

        # Only assign if changed -> prevents unnecessary rerenders.
        if self.open_files != open_files:
            self.open_files = open_files
        if self.active_file != active_file:
            self.active_file = active_file
        if self.dirty_by_file != dirty_by_file:
            self.dirty_by_file = dirty_by_file

    def set_editor_text(self, text: str) -> None:
        """Replace editor text programmatically (e.g. on tab switch)."""
        editor = self._get_editor()
        self._suspend_change_event = True
        editor.load_text(text)
        self._suspend_change_event = False

    # --- reactive watchers ---

    def watch_open_files(self, old, new) -> None:
        self._render_tabs()

    def watch_active_file(self, old, new) -> None:
        self._render_tabs()

    def watch_dirty_by_file(self, old, new) -> None:
        self._render_tabs()

    # --- rendering ---

    def _render_tabs(self) -> None:
        tabs = self._get_tabs_container()
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
            tab_key = self._stable_key(path)
            tab_id = self._tab_button_id(tab_key)
            close_id = self._close_button_id(tab_key)

            self._btn_to_path[tab_id] = path
            self._btn_to_path[close_id] = path

            tabs.mount(
                TabItem(
                    TabItemModel(
                        path=path,
                        active=(path == self.active_file),
                        dirty=bool(self.dirty_by_file.get(path, False)),
                        key=tab_key,
                    )
                )
            )

    @staticmethod
    def _stable_key(path: Path) -> str:
        # Stable across renders: do NOT append render generation.
        return hashlib.sha1(path.as_posix().encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _tab_button_id(key: str) -> str:
        return f"tab_{key}"

    @staticmethod
    def _close_button_id(key: str) -> str:
        return f"close_{key}"

    # --- event handlers ---

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
        self.post_message(BufferEdited(self.active_file, event.text_area.text))

    # --- small helpers ---

    def _get_tabs_container(self) -> Horizontal:
        return self.query_one(self._TABS_SEL, Horizontal)

    def _get_editor(self) -> TextArea:
        return self.query_one(self._EDITOR_SEL, TextArea)
