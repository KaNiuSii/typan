from __future__ import annotations

import os
import sys
import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional, Protocol


class TerminalBackend(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def send(self, data: str) -> None: ...
    def read_nonblocking(self, max_bytes: int = 65536) -> str: ...
    def is_alive(self) -> bool: ...


@dataclass
class TerminalConfig:
    cwd: Optional[str] = None
    cols: int = 120
    rows: int = 30


class WinPtyBackend:
    """
    Windows PTY backend via pywinpty (package: pywinpty).

    - read() bywa blokujące -> czytamy w osobnym wątku
    - UI robi tylko drain() z kolejki w timerze
    """

    def __init__(self, argv: list[str], cfg: TerminalConfig) -> None:
        self.argv = argv
        self.cfg = cfg

        self.proc = None
        self._q: "queue.Queue[str]" = queue.Queue()
        self._stop = threading.Event()
        self._reader_thread: threading.Thread | None = None

    def start(self) -> None:
        # pywinpty
        from winpty import PtyProcess

        if self.proc is not None:
            return

        self.proc = PtyProcess.spawn(
            self.argv,
            cwd=self.cfg.cwd or os.getcwd(),
            dimensions=(self.cfg.rows, self.cfg.cols),
        )

        self._stop.clear()
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _reader_loop(self) -> None:
        assert self.proc is not None
        while not self._stop.is_set():
            try:
                data = self.proc.read(65536)
                if data:
                    self._q.put(data)
                else:
                    time.sleep(0.01)
            except Exception:
                break

    def stop(self) -> None:
        self._stop.set()

        if self.proc is not None:
            try:
                self.proc.terminate(force=True)
            except Exception:
                pass
            self.proc = None

    def send(self, data: str) -> None:
        if self.proc is None:
            return

        # WinPTY najlepiej znosi CRLF w PowerShellu
        data = data.replace("\r\n", "\n").replace("\n", "\r\n")
        self.proc.write(data)

    def read_nonblocking(self, max_bytes: int = 65536) -> str:
        if self.proc is None:
            return ""

        chunks: list[str] = []
        total = 0
        try:
            while True:
                part = self._q.get_nowait()
                if not part:
                    continue
                chunks.append(part)
                total += len(part)
                if total >= max_bytes:
                    break
        except queue.Empty:
            pass

        return "".join(chunks)

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.isalive()


def default_shell_argv() -> list[str]:
    init = (
        "try { Remove-Module PSReadLine -ErrorAction SilentlyContinue } catch {};"
        "$ProgressPreference='SilentlyContinue';"
    )
    return [
        "powershell",
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-NoExit",
        "-Command",
        init,
    ]



def make_backend(
    argv: Optional[list[str]] = None,
    cfg: Optional[TerminalConfig] = None,
) -> TerminalBackend:
    if not sys.platform.startswith("win"):
        raise RuntimeError("This build currently supports Windows only.")
    argv = argv or default_shell_argv()
    cfg = cfg or TerminalConfig()
    return WinPtyBackend(argv, cfg)
