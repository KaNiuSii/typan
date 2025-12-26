from __future__ import annotations
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer

from typan_lab.widgets.project_tree import ProjectTree, OpenFileRequested
from typan_lab.widgets.editor_tabs import EditorTabs, BufferEdited, TabClosed, ActiveTabRequested
from typan_lab.widgets.terminal_panel import TerminalPanel
from typan_lab.widgets.status_bar import StatusBar

class WorkspaceScreen(Screen):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("ctrl+w", "close_tab", "Close tab", priority=True),
        Binding("ctrl+p", "command_palette", "Command", priority=True),
    ]

    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root

    def compose(self) -> ComposeResult:
        with Vertical(id="workspace-root"):
            with Horizontal(id="workspace-main"):
                yield ProjectTree(self.project_root, id="left")

                with Vertical(id="right"):
                    yield EditorTabs(id="editor")
                    yield TerminalPanel(id="terminal")

            yield StatusBar(id="status")
            yield Footer()

    # ---- routing-ish actions ----
    def action_command_palette(self) -> None:
        # Later: implement a modal/screen for commands
        self.query_one(TerminalPanel).write("\n> Ctrl+P pressed (command palette stub)\n")

    def action_close_tab(self) -> None:
        editor = self.query_one(EditorTabs)
        if editor.active_file is not None:
            self._close_file(editor.active_file)

    def action_save(self) -> None:
        app = self.app  # type: ignore
        state = app.state
        if state.active_file is None:
            return
        buf = state.buffers.get(state.active_file)
        if buf is None:
            return
        app.buffer_service.save_text(buf.path, buf.text)
        buf.dirty = False
        self._sync_status()

    # ---- message handlers (UI glue) ----
    def on_open_file_requested(self, msg: OpenFileRequested) -> None:
        self._open_file(msg.path)

    def on_active_tab_requested(self, msg: ActiveTabRequested) -> None:
        self._activate_file(msg.path)

    def on_tab_closed(self, msg: TabClosed) -> None:
        self._close_file(msg.path)

    def on_buffer_edited(self, msg: BufferEdited) -> None:
        app = self.app  # type: ignore
        state = app.state
        buf = state.buffers.get(msg.path)
        if buf is None:
            return
        buf.text = msg.text
        buf.dirty = True
        self._sync_status()

    # ---- internal helpers ----
    def _open_file(self, path: Path) -> None:
        app = self.app  # type: ignore
        state = app.state

        if not path.is_file():
            return

        text = app.buffer_service.open_text(path)
        buf = state.ensure_buffer(path, text)

        if path not in state.open_files:
            state.open_files.append(path)
        state.active_file = path

        editor = self.query_one(EditorTabs)
        editor.set_buffer(path, buf.text)
        self._sync_status()

    def _activate_file(self, path: Path) -> None:
        app = self.app  # type: ignore
        state = app.state
        if path not in state.open_files:
            return
        state.active_file = path

        editor = self.query_one(EditorTabs)
        buf = state.buffers.get(path)
        if buf:
            editor.active_file = path
            editor.update_buffer_text(path, buf.text)
        self._sync_status()

    def _close_file(self, path: Path) -> None:
        app = self.app  # type: ignore
        state = app.state

        if path in state.open_files:
            state.open_files.remove(path)

        editor = self.query_one(EditorTabs)

        # pick new active
        if state.active_file == path:
            state.active_file = state.open_files[-1] if state.open_files else None

        editor.open_files = list(state.open_files)
        editor.active_file = state.active_file
        if state.active_file:
            buf = state.buffers.get(state.active_file)
            if buf:
                editor.update_buffer_text(buf.path, buf.text)
        else:
            editor.clear()

        self._sync_status()

    def _sync_status(self) -> None:
        app = self.app  # type: ignore
        state = app.state
        status = self.query_one(StatusBar)
        status.active_file = state.active_file
        status.dirty = bool(state.active_file and state.buffers.get(state.active_file, None) and state.buffers[state.active_file].dirty)
        editor = self.query_one(EditorTabs)
        editor.dirty_by_file = {p: state.buffers[p].dirty for p in state.open_files if p in state.buffers}