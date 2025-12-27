from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Label

from typan_lab.widgets.styled_directory_tree import StyledDirectoryTree


# ---------------- Messages ----------------

class OpenFileRequested(Message):
    bubble = True
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

class RefreshRequested(Message):
    bubble = True

class CreateFileRequested(Message):
    bubble = True
    def __init__(self, parent_dir: Path) -> None:
        super().__init__()
        self.parent_dir = parent_dir

class CreateFolderRequested(Message):
    bubble = True
    def __init__(self, parent_dir: Path) -> None:
        super().__init__()
        self.parent_dir = parent_dir

class RenamePathRequested(Message):
    bubble = True
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

class DeletePathRequested(Message):
    bubble = True
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path


# ---------------- Config ----------------

@dataclass(frozen=True)
class ProjectTreeConfig:
    root: Path


# ---------------- Widget ----------------

class ProjectTree(Widget):
    """Project explorer panel with a toolbar + DirectoryTree."""

    def __init__(self, root: Path, *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        self._root = root
        self._selected: Path | None = None
        self._last_active: Path | None = None
        self._last_dirty: dict[Path, bool] = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            # Toolbar (VS Code-ish)
            with Horizontal(id="project-toolbar"):
                yield Label("EXPLORER", id="project-title")
                yield Button("↻", id="pt-refresh", classes="pt-btn", tooltip="Refresh")
                yield Button("+F", id="pt-new-file", classes="pt-btn", tooltip="New File")
                yield Button("+D", id="pt-new-dir", classes="pt-btn", tooltip="New Folder")
                yield Button("✎", id="pt-rename", classes="pt-btn", tooltip="Rename")
                yield Button("🗑", id="pt-delete", classes="pt-btn", tooltip="Delete")

            yield StyledDirectoryTree(str(self._root), id="dir-tree")

    # ---------- public helpers ----------

    def selected_path(self) -> Path | None:
        return self._selected

    def selected_dir(self) -> Path:
        """Directory where 'create' actions should happen."""
        if self._selected is None:
            return self._root
        if self._selected.is_dir():
            return self._selected
        return self._selected.parent

    async def reload_tree(self) -> None:
        tree = self.query_one("#dir-tree", StyledDirectoryTree)

        expanded = self._collect_expanded_dirs(tree)

        parent = tree.parent
        await tree.remove()

        new_tree = StyledDirectoryTree(str(self._root), id="dir-tree")
        await parent.mount(new_tree)

        new_tree.set_active_file(self._last_active)
        new_tree.set_dirty_map(self._last_dirty)

        await self._restore_expanded_dirs(new_tree, expanded)

    def set_active_file(self, path: Path | None) -> None:
        self._last_active = path
        self.query_one("#dir-tree", StyledDirectoryTree).set_active_file(path)

    def set_dirty_map(self, dirty_by_file: dict[Path, bool]) -> None:
        self._last_dirty = dict(dirty_by_file)
        self.query_one("#dir-tree", StyledDirectoryTree).set_dirty_map(dirty_by_file)

    def _collect_expanded_dirs(self, tree: StyledDirectoryTree) -> set[str]:
        """Zwraca zbiór ścieżek (as_posix) katalogów, które są rozwinięte."""
        expanded: set[str] = set()

        root = getattr(tree, "root", None)
        if root is None:
            return expanded

        def walk(node) -> None:
            data = getattr(node, "data", None)
            p = Path(getattr(data, "path", "")) if data is not None else None

            # sprawdź czy node jest rozwinięty (różne wersje mają różne nazwy)
            is_expanded = bool(
                getattr(node, "is_expanded", False)
                or getattr(node, "expanded", False)
                or getattr(node, "_expanded", False)
            )

            if p and p.exists() and p.is_dir() and is_expanded:
                expanded.add(p.resolve().as_posix())

            for child in getattr(node, "children", []) or []:
                walk(child)

        walk(root)
        return expanded

    async def _restore_expanded_dirs(self, tree: StyledDirectoryTree, expanded: set[str]) -> None:
        if not expanded:
            return

        root = getattr(tree, "root", None)
        if root is None:
            return

        async def walk(node) -> None:
            data = getattr(node, "data", None)
            p = Path(getattr(data, "path", "")) if data is not None else None

            if p and p.exists() and p.is_dir() and p.resolve().as_posix() in expanded:
                # spróbuj typowych metod rozwijania
                if hasattr(node, "expand"):
                    res = node.expand()
                    if asyncio.iscoroutine(res):
                        await res
                elif hasattr(node, "toggle"):
                    res = node.toggle()
                    if asyncio.iscoroutine(res):
                        await res

            for child in getattr(node, "children", []) or []:
                await walk(child)

        import asyncio
        await walk(root)
    # ---------- events ----------

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self._selected = Path(event.path)
        self.post_message(OpenFileRequested(self._selected))

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self._selected = Path(event.path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "pt-refresh":
            self.post_message(RefreshRequested())
        elif bid == "pt-new-file":
            self.post_message(CreateFileRequested(self.selected_dir()))
        elif bid == "pt-new-dir":
            self.post_message(CreateFolderRequested(self.selected_dir()))
        elif bid == "pt-rename":
            if self._selected:
                self.post_message(RenamePathRequested(self._selected))
        elif bid == "pt-delete":
            if self._selected:
                self.post_message(DeletePathRequested(self._selected))
