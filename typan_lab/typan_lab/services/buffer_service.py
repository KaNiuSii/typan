from __future__ import annotations
from pathlib import Path

class BufferService:
    def open_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")

    def save_text(self, path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
