from __future__ import annotations
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from typan_lab.screens.dir_picker import DirectoryPickerModal


class WelcomeScreen(Screen):
    BINDINGS = [("q", "quit", "Quit"), ("enter", "open_project", "Open")]

    def compose(self) -> ComposeResult:
        with Vertical(id="welcome-root"):
            with Vertical(id="welcome-card"):
                yield Static("TypanLab", id="title")
                yield Static("Select a project folder to start.", id="subtitle")

                with Horizontal(id="path-row"):
                    yield Input(placeholder="Project root path…", id="path")
                    yield Button("Choose…", id="choose")

                with Horizontal(id="actions"):
                    yield Button("Exit", id="exit")
                    yield Button("Open", id="open", variant="primary")

                yield Static("", id="hint")

    def on_mount(self) -> None:
        self.query_one("#hint", Static).update("Tip: Click “Choose…” or paste a path, then Open.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "choose":
            self._open_picker()
        elif bid == "open":
            self._open_project()
        elif bid == "exit":
            self.app.exit()

    def action_open_project(self) -> None:
        # Enter jako skrót (opcjonalnie)
        self._open_project()

    def _open_picker(self) -> None:
        current = self.query_one("#path", Input).value.strip()
        start = Path(current).expanduser() if current else Path.home()

        def on_done(result: Path | None) -> None:
            if result is None:
                return
            self.query_one("#path", Input).value = str(result)

        self.app.push_screen(DirectoryPickerModal(start=start), on_done)

    def _open_project(self) -> None:
        raw = self.query_one("#path", Input).value.strip()
        if not raw:
            self.notify("Podaj ścieżkę do folderu.", severity="warning")
            return

        root = Path(raw).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            self.notify("To nie jest poprawny folder.", severity="error")
            return

        self.app.open_workspace(root)
