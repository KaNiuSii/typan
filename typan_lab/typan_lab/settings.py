from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

IndentStyle = Literal["spaces", "tabs"]

@dataclass
class Settings:
    indent_style: IndentStyle = "spaces"
    indent_size: int = 4
