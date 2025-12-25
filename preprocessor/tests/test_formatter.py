from __future__ import annotations

import pytest
from formatter import format_text


def test_formatter_refuses_on_syntax_error():
    with pytest.raises(SyntaxError):
        format_text("}\n")


def test_formatter_formats_basic_indent_and_braces():
    src = "if x{\nprint(1)\n}\n"
    out = format_text(src)
    assert out == "if x {\n    print(1)\n}\n"


def test_formatter_splits_close_else_open():
    src = "if x{\na=1\n}else{\na=2\n}\n"
    out = format_text(src)
    assert out == "if x {\n    a=1\n}\nelse {\n    a=2\n}\n"


def test_formatter_idempotent():
    src = "if x{\nprint(1)\n}\n"
    out1 = format_text(src)
    out2 = format_text(out1)
    assert out1 == out2
