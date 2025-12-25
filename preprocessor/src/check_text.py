# check.py
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Optional

from preprocess import preprocess_text


@dataclass
class Diagnostic:
    stage: str            # "preprocess" | "python"
    message: str
    lineno: Optional[int] = None
    col: Optional[int] = None


def _diag_from_syntax_error(stage: str, e: SyntaxError) -> Diagnostic:
    # SyntaxError może mieć: msg, lineno, offset, text, end_lineno, end_offset
    msg = getattr(e, "msg", None) or (e.args[0] if e.args else "SyntaxError")
    lineno = getattr(e, "lineno", None)
    offset = getattr(e, "offset", None)
    return Diagnostic(stage=stage, message=str(msg), lineno=lineno, col=offset)


def check_text(text: str, *, indent: str = "    ") -> tuple[bool, list[Diagnostic], str | None]:
    """
    Zwraca:
      - ok: bool
      - diagnostics: lista Diagnostic
      - transformed: wynik preprocessora jeśli etap 1 przeszedł, inaczej None
    """
    # 1) Preprocessor
    try:
        transformed = preprocess_text(text, indent=indent)
    except SyntaxError as e:
        # preprocess_text już formatuje błąd (format_error) jeśli ma line/col,
        # więc message będzie “ładne”.
        return False, [Diagnostic(stage="preprocess", message=str(e))], None

    # 2) Python (AST parse)
    try:
        compile(transformed, filename="<typan>", mode="exec")
    except SyntaxError as e:
        return False, [_diag_from_syntax_error("python", e)], transformed

    return True, [], transformed
