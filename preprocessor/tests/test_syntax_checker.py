from __future__ import annotations

import pytest

from syntax_checker import check_text


def assert_preprocess_error(src: str, contains: str | None = None):
    ok, diags, transformed = check_text(src)
    assert ok is False
    assert transformed is None
    assert diags, "expected diagnostics"
    d = diags[0]
    assert d.stage == "preprocess"
    if contains:
        assert contains in d.message


def assert_python_error(
    src: str,
    contains: str | None = None,
    *,
    contains_any: list[str] | None = None,
    line: int | None = None,
):
    ok, diags, transformed = check_text(src)
    assert ok is False
    assert transformed is not None
    assert diags, "expected diagnostics"
    d = diags[0]
    assert d.stage == "python"

    if contains is not None:
        assert contains in d.message
    if contains_any is not None:
        assert any(s in d.message for s in contains_any), f"{d.message!r} not in {contains_any!r}"

    if line is not None:
        assert d.lineno == line



def test_ok_when_both_stages_ok():
    code = """\
if x {
print("ok")
}
"""
    ok, diags, transformed = check_text(code)
    assert ok is True
    assert diags == []
    assert transformed is not None
    assert "if x:" in transformed
    assert 'print("ok")' in transformed


def test_preprocess_error_unmatched_closing_brace_wins():
    # preprocessor ma wykryć '}' i zwrócić swój błąd
    assert_preprocess_error("}\n", contains="Unmatched")


def test_preprocess_error_missing_closing_brace_wins():
    code = """\
if x {
print(1)
"""
    assert_preprocess_error(code, contains="Missing closing")


def test_python_error_is_reported_only_after_preprocess_passes():
    # preprocessor to przepuści (prawidłowe bloki), ale wynikowy python ma błąd:
    # "return" poza funkcją
    code = """\
if x {
return 1
}
"""
    assert_python_error(code, contains="'return' outside function")


def test_python_error_invalid_syntax_in_transformed_code():
    code = """\
def f {
pass
}
"""
    assert_python_error(code, contains_any=["invalid syntax", "expected '('"])



def test_preprocess_error_has_priority_even_if_python_would_also_fail():
    # Tu jest błąd preprocessora (brak '}').
    # Nawet jeśli w środku byłby pythonowy błąd, checker ma zwrócić preprocess.
    code = """\
if x {
return 1
"""
    assert_preprocess_error(code, contains="Missing closing")


def test_transformed_is_returned_on_python_error():
    code = """\
if x {
return 1
}
"""
    ok, diags, transformed = check_text(code)
    assert ok is False
    assert transformed is not None
    # Przydatne do debugowania (np. --show-transformed)
    assert "if x:" in transformed


def test_indent_parameter_affects_transformed_output():
    code = """\
if x {
print(1)
}
"""
    ok, diags, transformed = check_text(code, indent="  ")
    assert ok is True
    assert diags == []
    assert transformed is not None
    assert "if x:" in transformed
    assert "\n  print(1)\n" in transformed


def test_python_error_line_number_is_present_when_possible():
    # Zwykle lineno będzie sensowne, jeśli emit zachowuje liczbę linii.
    # "break" poza pętlą: python SyntaxError z lineno.
    code = """\
if x {
break
}
"""
    ok, diags, transformed = check_text(code)
    assert ok is False
    assert transformed is not None
    d = diags[0]
    assert d.stage == "python"
    assert d.lineno is not None
