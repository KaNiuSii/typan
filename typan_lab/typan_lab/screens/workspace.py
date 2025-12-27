from __future__ import annotations

from pathlib import Path

import asyncio
import shutil

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer

from typan_lab.widgets.horizontal_split_handle import HorizontalSplitHandle
from typan_lab.widgets.vertical_split_handle import VerticalSplitHandle
from typan_lab.widgets.terminal_panel import TerminalPanel
from typan_lab.widgets.status_bar import StatusBar

from typan_lab.widgets.editor_panel import EditorPanel

from typan_lab.widgets.tab_bar import TabClosed, ActiveTabRequested
from typan_lab.widgets.editor_pane import BufferEdited

from typan_lab.modals.name_prompt_modal import NamePromptModal, NamePromptResult
from typan_lab.modals.confirm_modal import ConfirmModal, ConfirmResult

from typan_lab.widgets.project_tree import (
    ProjectTree,
    OpenFileRequested,
    RefreshRequested,
    CreateFileRequested,
    CreateFolderRequested,
    RenamePathRequested,
    DeletePathRequested,
)

class WorkspaceScreen(Screen):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("ctrl+w", "close_tab", "Close tab", priority=True),
        Binding("ctrl+p", "command_palette", "Command", priority=True),
    ]

    left_width: reactive[int] = reactive(32)
    editor_weight: reactive[int] = reactive(1)
    terminal_weight: reactive[int] = reactive(12)

    def _run_async(self, coro) -> None:
        asyncio.create_task(coro)

    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root

    def compose(self) -> ComposeResult:
        with Vertical(id="workspace-root"):
            with Horizontal(id="workspace-main"):
                yield ProjectTree(self.project_root, id="left")
                yield VerticalSplitHandle(min_width=18, max_width=80, id="left-split")
                with Vertical(id="right"):
                    yield EditorPanel(id="editor")
                    yield HorizontalSplitHandle(id="editor-terminal-split")
                    yield TerminalPanel(id="terminal")

            yield StatusBar(id="status")
            yield Footer()

    def on_mount(self) -> None:
        app = self.app  # type: ignore
        state = app.state

        term = self.query_one(TerminalPanel)
        term.set_cwd(state.project_root)
        term.start_terminal()

        self._sync_tabs_and_status()
        self._sync_editor_text()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

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

    async def on_refresh_requested(self, msg: RefreshRequested) -> None:
        await self.query_one(ProjectTree).reload_tree()

    async def _create_file(self, parent: Path, name: str) -> None:
        name = name.strip()
        if not name:
            return
        new_path = parent / name
        if new_path.exists():
            self.query_one(TerminalPanel).write(f"\n> File already exists: {new_path}\n")
            return
        new_path.write_text("", encoding="utf-8")
        await self.query_one(ProjectTree).reload_tree()

    async def on_create_file_requested(self, msg: CreateFileRequested) -> None:
        parent = msg.parent_dir

        def after(result: NamePromptResult | None) -> None:
            if result is None:
                return
            self._run_async(self._create_file(parent, result.name))

        await self.app.push_screen(NamePromptModal("New File", placeholder="filename.ext"), after)

    async def _create_folder(self, parent: Path, name: str) -> None:
        name = name.strip()
        if not name:
            return
        new_path = parent / name
        if new_path.exists():
            self.query_one(TerminalPanel).write(f"\n> Folder already exists: {new_path}\n")
            return
        new_path.mkdir(parents=True, exist_ok=False)
        await self.query_one(ProjectTree).reload_tree()

    async def on_create_folder_requested(self, msg: CreateFolderRequested) -> None:
        parent = msg.parent_dir

        def after(result: NamePromptResult | None) -> None:
            if result is None:
                return
            self._run_async(self._create_folder(parent, result.name))

        await self.app.push_screen(NamePromptModal("New Folder", placeholder="folder name"), after)

    async def _rename_path(self, path: Path, parent: Path, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            return

        new_path = parent / new_name
        if new_path.exists():
            self.query_one(TerminalPanel).write(f"\n> Target already exists: {new_path}\n")
            return

        path.rename(new_path)

        # sync app state if renamed file was open
        app = self.app  # type: ignore
        state = app.state

        if path in state.open_files:
            idx = state.open_files.index(path)
            state.open_files[idx] = new_path

        if state.active_file == path:
            state.active_file = new_path

        if path in state.buffers:
            buf = state.buffers.pop(path)
            # jeśli Buffer.path jest modyfikowalne:
            try:
                buf.path = new_path
            except Exception:
                pass
            state.buffers[new_path] = buf

        await self.query_one(ProjectTree).reload_tree()
        self._sync_tabs_and_status()
        self._sync_editor_text()

    async def on_rename_path_requested(self, msg: RenamePathRequested) -> None:
        path = msg.path
        if not path.exists():
            return

        parent = path.parent
        initial = path.name

        def after(result: NamePromptResult | None) -> None:
            if result is None:
                return
            self._run_async(self._rename_path(path, parent, result.name))

        await self.app.push_screen(NamePromptModal("Rename", placeholder="new name", initial=initial), after)

    async def _delete_path(self, path: Path) -> None:
        app = self.app  # type: ignore
        state = app.state

        def close_if_open(p: Path) -> None:
            if p in state.open_files:
                state.open_files.remove(p)
            if state.active_file == p:
                state.active_file = state.open_files[-1] if state.open_files else None
            state.buffers.pop(p, None)

        if path.is_dir():
            # usuwa też niepuste
            shutil.rmtree(path)
        else:
            close_if_open(path)
            path.unlink()

        await self.query_one(ProjectTree).reload_tree()
        self._sync_tabs_and_status()
        self._sync_editor_text()

    async def on_delete_path_requested(self, msg: DeletePathRequested) -> None:
        path = msg.path
        if not path.exists():
            return

        def after(result: ConfirmResult) -> None:
            if not result.confirmed:
                return
            self._run_async(self._delete_path(path))

        await self.app.push_screen(
            ConfirmModal("Delete", f"Delete '{path.name}'?", yes_text="Delete", no_text="Cancel"),
            after,
        )

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    def on_horizontal_split_handle_split_dragged(self, msg: HorizontalSplitHandle.SplitDragged) -> None:
        right = self.query_one("#right")

        # pozycja Y splitu wewnątrz #right
        local_y = msg.screen_y - right.region.y

        # uwzględnij pasek splittera (ma 1-2 linie, zależnie od hover/drag)
        split = self.query_one(HorizontalSplitHandle)
        split_h = max(1, split.size.height)

        total = right.region.height - split_h
        if total <= 2:
            return

        min_editor = 6
        min_terminal = 6

        # clamp: editor min, terminal min
        editor_cells = max(min_editor, min(local_y, total - min_terminal))
        terminal_cells = max(min_terminal, total - editor_cells)

        # używamy fr jako “wagi” ~ liczbie linii
        self.editor_weight = editor_cells
        self.terminal_weight = terminal_cells
        self._apply_layout_sizes()

    def on_vertical_split_handle_split_dragged(self, msg: VerticalSplitHandle.SplitDragged) -> None:
        self.left_width = msg.new_width
        self._apply_layout_sizes()

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

    def _apply_layout_sizes(self) -> None:
        left = self.query_one("#left")
        editor = self.query_one("#editor")
        terminal = self.query_one("#terminal")

        left.styles.width = self.left_width

        editor.styles.height = f"{self.editor_weight}fr"
        terminal.styles.height = f"{self.terminal_weight}"

        self.refresh(layout=True)

    # ------------------------------------------------------------------
    # UI sync
    # ------------------------------------------------------------------

    def _sync_project_tree(self) -> None:
        app = self.app  # type: ignore
        state = app.state

        tree = self.query_one(ProjectTree)
        tree.set_active_file(state.active_file)
        dirty_map = {p: state.buffers[p].dirty for p in state.buffers.keys()}
        tree.set_dirty_map(dirty_map)

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

        self._sync_project_tree()


    def _sync_editor_text(self) -> None:
        app = self.app  # type: ignore
        state = app.state

        editor = self.query_one(EditorPanel)
        if state.active_file and state.active_file in state.buffers:
            editor.set_editor(active_file=state.active_file, text=state.buffers[state.active_file].text)
        else:
            editor.set_editor(active_file=None, text="")

        self._sync_project_tree()

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
        self._sync_project_tree()
