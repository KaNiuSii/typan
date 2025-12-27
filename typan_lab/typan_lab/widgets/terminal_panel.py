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

        self._try_activate_venv()

        self._inp.disabled = False
        self._inp.focus()


        self._poll_timer = self.set_interval(0.05, self._poll)

    def _try_activate_venv(self) -> None:
        """If .venv exists in cwd, activate it in the PowerShell session."""
        if not self._session or not self._cwd:
            return

        venv_dir = self._cwd / ".venv"
        if not venv_dir.exists() or not venv_dir.is_dir():
            return

        activate = venv_dir / "Scripts" / "Activate.ps1"
        if not activate.exists():
            return

        cmd = f'& "{activate}"'
        self._append(f"[venv] Activating: {venv_dir}\n")
        self._session.send_line(cmd)

        self._fetch_debug_typan()

    def _fetch_debug_typan(self) -> None:
        if not self._session or not self._cwd:
            return

        pkg_root = Path(r"C:\Users\Kacper\Desktop\typan\typan")
        if not pkg_root.exists():
            return

        if not (pkg_root / "pyproject.toml").exists() and not (pkg_root / "setup.py").exists():
            return

        self._append("[typan] Installing editable package...\n")

        try:
            self._session.send_line("python -m pip install -U pip setuptools wheel")

            self._session.send_line(f'pip install -e "{pkg_root}"')
        except Exception:
            self._append("[typan] Couldn't install package.\n")
            return

    def run_typan_file(self, path: Path, out_dir_name: str = "transpilled") -> None:
        if not self._session or not self._cwd:
            self._append("[ERROR] Terminal not ready.\n")
            return

        if path.suffix.lower() != ".ty":
            self._append(f"[WARN] Not a .ty file: {path.name}\n")
            return

        root = self._cwd
        out_dir = root / out_dir_name
        out_py = out_dir / f"{path.stem}.py"

        # 1) mkdir transpilled (Python-side, no shell bullshit)
        try:
            out_dir.mkdir(exist_ok=True)
        except Exception as e:
            self._append(f"[ERROR] Failed to create {out_dir}: {e}\n")
            return

        # 2) wrzucamy DWIE PROSTE KOMENDY do terminala
        self._append(f"\n[run] typan {path.name} -> {out_dir_name}/{out_py.name}\n")

        self._session.send_line(
            f'typan "{path}" -o "{out_py}"'
        )

        self._session.send_line(
            f'python "{out_py}"'
        )

    def format_typan_file(self, path: Path, indent_size: int = 4) -> None:
        """Run typan-fmt in-place on a .ty file."""
        if not self._session:
            self._append("[ERROR] Terminal not started.\n")
            return
        if path.suffix.lower() != ".ty":
            return

        # typan-fmt --indent expects an int string
        self._append(f"\n[fmt] typan-fmt --in-place {path.name}\n")
        self._session.send_line(
            f'typan-fmt "{path}" --in-place --indent {int(indent_size)}'
        )

    def run_python_file(self, path: Path) -> None:
        if not self._session:
            self._append("[ERROR] Terminal not started.\n")
            return
        self._append(f"\n[run] python {path.name}\n")
        self._session.send_line(f'python "{path}"')

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
