from __future__ import annotations
from pathlib import Path

class ProjectService:
    def list_files(self, root: Path) -> list[Path]:
        # Keep it simple: ignore hidden + common noisy dirs; customize later
        ignore = {".git", ".idea", ".vscode", "__pycache__", ".venv", "node_modules"}
        files: list[Path] = []
        for p in root.rglob("*"):
            if any(part in ignore for part in p.parts):
                continue
            if p.is_file():
                files.append(p)
        return sorted(files)
