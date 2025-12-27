from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from typan_lab.settings import Settings


@dataclass
class Buffer:
    path: Path
    text: str
    clean_text: str
    dirty: bool = False

    def set_text(self, new_text: str) -> None:
        self.text = new_text
        self.dirty = (self.text != self.clean_text)

    def mark_saved(self) -> None:
        self.clean_text = self.text
        self.dirty = False

@dataclass
class AppState:
    project_root: Path | None = None
    open_files: list[Path] = field(default_factory=list)
    active_file: Path | None = None
    buffers: dict[Path, Buffer] = field(default_factory=dict)
    settings: Settings = field(default_factory=Settings)
    fetch_debug_typan: bool = field(default=False)

    def ensure_buffer(self, path: Path, text: str) -> Buffer:
        buf = self.buffers.get(path)
        if buf is None:
            buf = Buffer(path=path, text=text, clean_text=text, dirty=False)
            self.buffers[path] = buf
        return buf
