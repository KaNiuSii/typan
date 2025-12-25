# cli_check.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from check_text import check_text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="typan-check", description="Check brace-python syntax.")
    p.add_argument("input", help="Input file path (brace syntax). Use '-' for stdin.")
    p.add_argument("--indent", default="4", help="Indent width in spaces (default: 4).")
    p.add_argument("--show-transformed", action="store_true", help="Print transformed code if python stage fails.")
    args = p.parse_args(argv)

    try:
        w = int(args.indent)
        if w < 0:
            raise ValueError
    except ValueError:
        print("typan-check: --indent must be a non-negative integer", file=sys.stderr)
        return 2

    indent = " " * w

    if args.input == "-":
        src = sys.stdin.read()
    else:
        src = Path(args.input).read_text(encoding="utf-8")

    ok, diags, transformed = check_text(src, indent=indent)

    if ok:
        return 0

    d = diags[0]
    # Priorytet: preprocessor. Jak go nie ma, to python.
    if d.stage == "preprocess":
        print(str(d.message), file=sys.stderr)
        return 1

    # python stage
    # Jak chcesz: pokaż błąd w stylu pythonowym z lineno/offset.
    loc = ""
    if d.lineno is not None and d.col is not None:
        loc = f"(line {d.lineno}, col {d.col}) "
    print(f"Python syntax error {loc}{d.message}", file=sys.stderr)

    if args.show_transformed and transformed is not None:
        print("\n--- transformed ---\n", file=sys.stderr)
        print(transformed, file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
