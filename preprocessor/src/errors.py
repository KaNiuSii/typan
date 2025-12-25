# errors.py
from __future__ import annotations

def format_error(source: str, line: int, col: int, message: str) -> str:
    """
    line, col are 1-based.
    """
    lines = source.splitlines()
    if line < 1 or line > len(lines):
        return f"{message} (line {line}, col {col})"

    src_line = lines[line - 1]
    caret_pos = max(0, col - 1)
    caret_pos = min(caret_pos, len(src_line))

    # keep it simple (no truncation yet)
    caret_line = " " * caret_pos + "^"

    return (
        f"{message} at line {line}, col {col}\n"
        f"{src_line}\n"
        f"{caret_line}"
    )
