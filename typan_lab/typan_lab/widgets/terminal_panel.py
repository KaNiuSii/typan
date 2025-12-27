from __future__ import annotations

import sys
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Input, TextArea

from typan_lab.terminal.session import TerminalSession
from typan_lab.terminal.backends import TerminalConfig
from typan_lab.terminal.ansi import strip_ansi


class TerminalPanel(Widget):
    MAX_CHARS = 300_000

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._session: TerminalSession | None = None
        self._poll_timer = None
        self._buffer: str = ""

        self._out: TextArea | None = None
        self._inp: Input | None = None

        self._cwd: Path | None = None

    def set_cwd(self, cwd: Path | None) -> None:
        """Ustaw katalog roboczy przed startem terminala."""
        self._cwd = cwd

    def compose(self) -> ComposeResult:
        with Vertical():
            yield TextArea("", read_only=True, id="terminal-out")
            yield Input(placeholder="type command and press Enter", id="terminal-in")

    def on_mount(self) -> None:
        self._out = self.query_one("#terminal-out", TextArea)
        self._inp = self.query_one("#terminal-in", Input)

        self._inp.disabled = True
        self._set_text("Starting PTY terminal...\n")

    def start_terminal(self):
        if self._session is not None:
            return
        if self._out is None or self._inp is None:
            return
        try:
            cfg = TerminalConfig(cwd=str(self._cwd) if self._cwd else None)
            self._session = TerminalSession.create(cfg=cfg)
            self._session.start()
        except ModuleNotFoundError as e:
            self._append("\n[ERROR] Terminal backend dependency missing.\n")
            self._append(f"{type(e).__name__}: {e}\n\n")
            if sys.platform.startswith("win"):
                self._append("Install: pip install pywinpty\n")
            else:
                self._append("Install: pip install pexpect\n")
            self._append("\nTerminal disabled.\n")
            self._session = None
            return
        except Exception as e:
            self._append("\n[ERROR] Failed to start terminal session.\n")
            self._append(f"{type(e).__name__}: {e}\n")
            self._append("\nTerminal disabled.\n")
            self._session = None
            return

        self._append("PTY terminal ready.\n")
        self._inp.disabled = False
        self._inp.focus()

        self._poll_timer = self.set_interval(0.05, self._poll)

    def on_unmount(self) -> None:
        if self._poll_timer is not None:
            try:
                self._poll_timer.stop()
            except Exception:
                pass
            self._poll_timer = None

        if self._session:
            self._session.stop()
            self._session = None

    def _poll(self) -> None:
        if not self._session or not self._session.is_alive():
            return

        chunk = self._session.drain(max_bytes=50_000)
        if not chunk:
            return

        self._append(strip_ansi(chunk))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self._session:
            return

        line = event.value.rstrip("\r\n")
        event.input.value = ""

        if not line.strip():
            return

        self._append(f"PS> {line}\n")
        self._session.send_line(line)

    # --- buffer helpers ---

    def _set_text(self, text: str) -> None:
        self._buffer = text
        if self._out is None:
            return
        self._out.load_text(self._buffer)
        self._out.scroll_end(animate=False)

    def _append(self, text: str) -> None:
        if not text:
            return

        self._buffer += text
        if len(self._buffer) > self.MAX_CHARS:
            self._buffer = self._buffer[-self.MAX_CHARS :]

        if self._out is None:
            return

        self._out.load_text(self._buffer)
        self._out.scroll_end(animate=False)
