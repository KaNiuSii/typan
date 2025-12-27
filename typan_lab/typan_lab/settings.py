from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

IndentStyle = Literal["spaces", "tabs"]
FormatMode = Literal["off", "on_save", "on_update"]

@dataclass
class Settings:
    indent_style: IndentStyle = "spaces"
    indent_size: int = 4
    format_mode: FormatMode = "off"
