from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Route:
    name: str
    params: dict
