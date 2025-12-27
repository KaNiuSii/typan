from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .backends import TerminalBackend, TerminalConfig, make_backend


@dataclass
class TerminalSession:
    backend: TerminalBackend

    @classmethod
    def create(
        cls,
        argv: Optional[list[str]] = None,
        cfg: Optional[TerminalConfig] = None,
    ) -> "TerminalSession":
        return cls(backend=make_backend(argv=argv, cfg=cfg))

    def start(self) -> None:
        self.backend.start()

    def stop(self) -> None:
        self.backend.stop()

    def send_text(self, text: str) -> None:
        self.backend.send(text)

    def send_line(self, line: str) -> None:
        self.backend.send(line + "\n")

    def drain(self, max_bytes: int = 65536) -> str:
        return self.backend.read_nonblocking(max_bytes=max_bytes)

    def is_alive(self) -> bool:
        return self.backend.is_alive()
