from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path

from typan_lab.settings import Settings

class PreferencesService:
    def __init__(self, app_name: str = "TypanLab") -> None:
        # Windows: %APPDATA%/TypanLab/prefs.json
        base = Path.home() / "AppData" / "Roaming" / app_name
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "prefs.json"

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        # defensywnie:
        return Settings(
            indent_style=data.get("indent_style", "spaces"),
            indent_size=int(data.get("indent_size", 4)),
        )

    def save(self, settings: Settings) -> None:
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
