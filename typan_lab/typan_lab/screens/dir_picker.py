from __future__ import annotations
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Static


class DirectoryPicked(Message):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path


class DirectoryPickerModal(ModalScreen[Path | None]):
    """Modal do wybrania katalogu. Zwraca Path albo None (cancel)."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, start: Path | None = None) -> None:
        super().__init__()
        self.start = start or Path.home()

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Static("Choose root directory", id="modal-title")

            yield DirectoryTree(str(self.start), id="tree")

            with Horizontal(id="modal-actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Select", id="select", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "select":
            self._select_current()

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        # opcjonalnie: podwójny klik/enter mógłby od razu wybierać
        pass

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _select_current(self) -> None:
        tree = self.query_one("#tree", DirectoryTree)
        # DirectoryTree trzyma "cursor_node"; bierzemy jego path
        node = tree.cursor_node
        if node is None:
            self.dismiss(None)
            return

        path = Path(str(node.data.path))  # data.path jest string/path zależnie od wersji
        if path.exists() and path.is_dir():
            self.dismiss(path)
        else:
            self.notify("Please select a directory.", severity="warning")
