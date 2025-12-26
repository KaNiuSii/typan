from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer

from typan_lab.widgets.project_tree import ProjectTree, OpenFileRequested
from typan_lab.widgets.terminal_panel import TerminalPanel
from typan_lab.widgets.status_bar import StatusBar

from typan_lab.widgets.editor_panel import EditorPanel

from typan_lab.widgets.tab_bar import TabClosed, ActiveTabRequested
from typan_lab.widgets.editor_pane import BufferEdited


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
                    yield EditorPanel(id="editor")
                    yield TerminalPanel(id="terminal")

            yield StatusBar(id="status")
            yield Footer()

    def on_mount(self) -> None:
        self._sync_tabs_and_status()
        self._sync_editor_text()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_command_palette(self) -> None:
        self.query_one(TerminalPanel).write(
            "\n> Ctrl+P pressed (command palette stub)\n"
        )

    def action_close_tab(self) -> None:
        app = self.app  # type: ignore
        state = app.state
        if state.active_file is None:
            return
        self._close_file(state.active_file)

    def action_save(self) -> None:
        app = self.app  # type: ignore
        state = app.state

        if state.active_file is None:
            return

        buf = state.buffers.get(state.active_file)
        if buf is None:
            return

        app.buffer_service.save_text(buf.path, buf.text)

        buf.clean_text = buf.text
        buf.dirty = False

        self._sync_tabs_and_status()

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    def on_open_file_requested(self, msg: OpenFileRequested) -> None:
        self._open_file(msg.path)

    def on_active_tab_requested(self, msg: ActiveTabRequested) -> None:
        self._activate_file(msg.path)

    def on_tab_closed(self, msg: TabClosed) -> None:
        self._close_file(msg.path)

    def on_buffer_edited(self, msg: BufferEdited) -> None:
        """
        Called for every keystroke -> do minimal work.
        Do NOT reload TextArea here.
        """
        app = self.app  # type: ignore
        state = app.state

        buf = state.buffers.get(msg.path)
        if buf is None:
            return

        prev_dirty = buf.dirty
        buf.text = msg.text
        buf.dirty = (buf.text != buf.clean_text)

        if buf.dirty != prev_dirty:
            self._sync_tabs_and_status()
        else:
            self._sync_status_only()

    # ------------------------------------------------------------------
    # State mutations
    # ------------------------------------------------------------------

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

        # open from disk => not dirty
        buf.clean_text = buf.text
        buf.dirty = False

        self._sync_tabs_and_status()
        self._sync_editor_text()

    def _activate_file(self, path: Path) -> None:
        app = self.app  # type: ignore
        state = app.state

        if path not in state.open_files:
            return

        state.active_file = path

        self._sync_tabs_and_status()
        self._sync_editor_text()

    def _close_file(self, path: Path) -> None:
        app = self.app  # type: ignore
        state = app.state

        if path in state.open_files:
            state.open_files.remove(path)

        if state.active_file == path:
            state.active_file = state.open_files[-1] if state.open_files else None

        self._sync_tabs_and_status()
        self._sync_editor_text()

    # ------------------------------------------------------------------
    # UI sync
    # ------------------------------------------------------------------

    def _sync_tabs_and_status(self) -> None:
        app = self.app  # type: ignore
        state = app.state

        # status bar
        status = self.query_one(StatusBar)
        status.active_file = state.active_file
        status.dirty = bool(
            state.active_file
            and state.active_file in state.buffers
            and state.buffers[state.active_file].dirty
        )

        # tabs
        editor = self.query_one(EditorPanel)
        dirty_map = {
            p: state.buffers[p].dirty
            for p in state.open_files
            if p in state.buffers
        }
        editor.set_tabs(state.open_files, state.active_file, dirty_map)

    def _sync_editor_text(self) -> None:
        app = self.app  # type: ignore
        state = app.state

        editor = self.query_one(EditorPanel)
        if state.active_file and state.active_file in state.buffers:
            editor.set_editor(active_file=state.active_file, text=state.buffers[state.active_file].text)
        else:
            editor.set_editor(active_file=None, text="")

    def _sync_status_only(self) -> None:
        app = self.app  # type: ignore
        state = app.state

        status = self.query_one(StatusBar)
        status.active_file = state.active_file
        status.dirty = bool(
            state.active_file
            and state.active_file in state.buffers
            and state.buffers[state.active_file].dirty
        )
