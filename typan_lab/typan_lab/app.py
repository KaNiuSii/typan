# typan_lab/app.py
from __future__ import annotations
import os
from pathlib import Path
from typing import ClassVar

import importlib.resources as ir

from textual.app import App
from textual.reactive import reactive

from typan_lab.screens.settings import SettingsScreen
from typan_lab.state import AppState
from typan_lab.services.preferences_service import PreferencesService
from typan_lab.services.project_service import ProjectService
from typan_lab.services.buffer_service import BufferService
from typan_lab.screens.workspace import WorkspaceScreen
from typan_lab.screens.welcome import WelcomeScreen

from typan_lab.style_loader import load_tcss, discover_tcss_near_py

_COMPONENT_REL = discover_tcss_near_py("typan_lab", subpackages=("screens", "widgets"))
_CSS_FILES = [str(ir.files(mod) / fname) for (mod, fname) in _COMPONENT_REL]

class TypanLabApp(App):
    state: AppState = reactive(AppState())
    CSS_PATH: ClassVar[list[str]] = []

    BINDINGS = [
        ("ctrl+comma", "open_settings", "Settings"),
    ]

    def __init__(self, project_root: Path | None = None) -> None:
        type(self).CSS_PATH = _CSS_FILES

        super().__init__()

        self.prefs = PreferencesService()
        self.project_service = ProjectService()
        self.buffer_service = BufferService()
        self._initial_root = project_root

        self.state.settings = self.prefs.load()
        self.apply_settings()

    def on_mount(self) -> None:
        # 1) jeśli root przyszedł z env/arg (np. TYPAN_ROOT) -> od razu workspace
        env_root = os.environ.get("TYPAN_ROOT")
        if env_root:
            root = Path(env_root).expanduser().resolve()
            if root.exists() and root.is_dir():
                self.open_workspace(root)
                return

        # 2) jeśli przekazany w __init__
        if self._initial_root and self._initial_root.exists() and self._initial_root.is_dir():
            self.open_workspace(self._initial_root.resolve())
            return

        # 3) domyślnie: ekran wyboru projektu
        self.push_screen(WelcomeScreen())

    def open_workspace(self, root: Path) -> None:
        self.state.project_root = root
        # czyścimy stos i ładujemy workspace “od zera”
        self.pop_screen() if self.screen else None
        self.push_screen(WorkspaceScreen(root))

    def action_open_settings(self) -> None:
        self.push_screen(SettingsScreen())

    def action_toggle_theme(self) -> None:
        s = self.state.settings
        self.apply_settings()
        self.save_settings()

    def apply_settings(self) -> None:
        pass

    def save_settings(self) -> None:
        self.prefs.save(self.state.settings)
