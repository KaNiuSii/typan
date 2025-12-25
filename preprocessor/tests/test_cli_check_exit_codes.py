from __future__ import annotations

import io

import pytest

from cli_check import main


def write(tmp_path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_exit_code_ok_for_valid_file(tmp_path, capsys):
    p = write(
        tmp_path,
        "ok.tp",
        """\
if x {
pass
}
""",
    )
    code = main([str(p)])
    out = capsys.readouterr()
    assert code == 0
    assert out.err == ""


def test_exit_code_1_for_preprocess_error(tmp_path, capsys):
    p = write(tmp_path, "bad.tp", "}\n")
    code = main([str(p)])
    out = capsys.readouterr()
    assert code == 1
    assert "Unmatched" in out.err


def test_exit_code_1_for_python_error(tmp_path, capsys):
    p = write(
        tmp_path,
        "pyerr.tp",
        """\
if x {
return 1
}
""",
    )
    code = main([str(p)])
    out = capsys.readouterr()
    assert code == 1
    assert "Python syntax error" in out.err
    assert "outside" in out.err  # "outside function" / "outside of a function"


def test_show_transformed_prints_transformed_on_python_error(tmp_path, capsys):
    p = write(
        tmp_path,
        "pyerr.tp",
        """\
if x {
return 1
}
""",
    )
    code = main([str(p), "--show-transformed"])
    out = capsys.readouterr()
    assert code == 1
    assert "--- transformed ---" in out.err
    assert "if x:" in out.err


def test_exit_code_2_for_missing_file(tmp_path, capsys):
    missing = tmp_path / "nope.tp"
    code = main([str(missing)])
    out = capsys.readouterr()
    assert code == 2
    assert "input file not found" in out.err


def test_exit_code_2_for_invalid_indent(capsys):
    code = main(["-", "--indent", "-1"])
    out = capsys.readouterr()
    assert code == 2
    assert "--indent must be a non-negative integer" in out.err


def test_stdin_mode_ok(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("if x { pass }\n"))
    code = main(["-"])
    out = capsys.readouterr()
    assert code == 0
    assert out.err == ""


def test_exit_code_2_for_unknown_flag(capsys):
    code = main(["--nope"])
    out = capsys.readouterr()
    assert code == 2
    # argparse pisze usage + error na stderr
    assert "usage:" in out.err.lower()
