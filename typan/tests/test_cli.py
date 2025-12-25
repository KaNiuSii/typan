# tests/test_cli.py
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest

from cli import main


def write(p: Path, s: str):
    p.write_text(s, encoding="utf-8", newline="\n")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_cli_stdout(tmp_path: Path, capsys):
    inp = tmp_path / "a.tp.py"
    write(inp, "if x {\nprint(1)\n}\n")
    rc = main([str(inp)])
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "if x:\n    print(1)\n"


def test_cli_output_file(tmp_path: Path):
    inp = tmp_path / "a.tp.py"
    outp = tmp_path / "out.py"
    write(inp, "if x {\nprint(1)\n}\n")
    rc = main([str(inp), "-o", str(outp)])
    assert rc == 0
    assert read(outp) == "if x:\n    print(1)\n"


def test_cli_in_place(tmp_path: Path):
    inp = tmp_path / "a.tp.py"
    write(inp, "if x {\n}\n")
    rc = main([str(inp), "--in-place"])
    assert rc == 0
    assert read(inp) == "if x:\n    pass\n"


def test_cli_check_exit_codes(tmp_path: Path):
    inp = tmp_path / "a.tp.py"
    write(inp, "if x {\n}\n")
    rc = main([str(inp), "--in-place", "--check"])
    assert rc == 1  # would change
    # file should remain unchanged in --check
    assert read(inp) == "if x {\n}\n"

    # already python: check should be 0
    write(inp, "if x:\n    pass\n")
    rc = main([str(inp), "--in-place", "--check"])
    assert rc == 0


def test_cli_stdin_to_stdout(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("if x {\nprint(1)\n}\n"))
    rc = main(["-"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "if x:\n    print(1)\n"


def test_cli_stdin_reject_in_place(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("if x {\n}\n"))
    rc = main(["-", "--in-place"])
    assert rc == 2


def test_cli_indent_option(tmp_path: Path):
    inp = tmp_path / "a.tp.py"
    write(inp, "if x {\nprint(1)\n}\n")
    rc = main([str(inp), "--indent", "2"])
    assert rc == 0
