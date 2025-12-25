from __future__ import annotations

from lex import lex
from lines import logical_lines
from errors import format_error
from transform import transform
from emit import emit


def preprocess_text(text: str, *, indent: str = "    ") -> str:
    try:
        tokens = lex(text)
        lines = logical_lines(tokens)
        events = transform(lines)
        return emit(events, indent_str=indent)
    except SyntaxError as e:
        # try extract "at line X, col Y" from args? we have better: raise SyntaxError with known coords.
        # We'll support two patterns:
        # 1) e.args[0] contains "... line {ln}, col {col}"
        # 2) e has attributes lineno/offset (sometimes)
        msg = e.args[0] if e.args else "SyntaxError"

        # Prefer lineno/offset if present
        ln = getattr(e, "lineno", None)
        col = getattr(e, "offset", None)

        # Fallback: parse simple pattern we use in transform
        if ln is None or col is None:
            import re
            m = re.search(r"line\s+(\d+),\s*col\s+(\d+)", msg)
            if m:
                ln = int(m.group(1))
                col = int(m.group(2))

        if ln is not None and col is not None:
            raise SyntaxError(format_error(text, ln, col, msg)) from None

        raise


def preprocess_file(in_path: str, out_path: str, *, indent: str = "    ") -> None:
    with open(in_path, "r", encoding="utf-8") as f:
        src = f.read()
    out = preprocess_text(src, indent=indent)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)


def preprocess_in_place(path: str, *, indent: str = "    ", check_only: bool = False) -> bool:
    """
    If check_only=True, does not write, returns True if file would change.
    If check_only=False, writes if changed, returns True if changed.
    """
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    if "{" not in src and "}" not in src:
        return False

    out = preprocess_text(src, indent=indent)

    changed = (out != src)
    if check_only:
        return changed

    if changed:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
    return changed
