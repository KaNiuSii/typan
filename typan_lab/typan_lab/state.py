from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from typan_lab.settings import Settings


@dataclass
class Buffer:
    path: Path
    text: str
    dirty: bool = False

@dataclass
class AppState:
    project_root: Path | None = None
    open_files: list[Path] = field(default_factory=list)
    active_file: Path | None = None
    buffers: dict[Path, Buffer] = field(default_factory=dict)
    settings: Settings = field(default_factory=Settings)

    def ensure_buffer(self, path: Path, text: str) -> Buffer:
        buf = self.buffers.get(path)
        if buf is None:
            buf = Buffer(path=path, text=text, dirty=False)
            self.buffers[path] = buf
        return buf
