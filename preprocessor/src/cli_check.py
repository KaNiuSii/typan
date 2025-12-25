from __future__ import annotations

import argparse
import sys
from pathlib import Path

from check_text import check_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="typan-check",
        description="typan-check: validate brace-python using typan preprocessor + Python compile() diagnostics.",
    )

    p.add_argument(
        "input",
        help="Input file path (brace syntax). Use '-' to read from stdin.",
    )

    p.add_argument(
        "--indent",
        default="4",
        help="Indent width in spaces (default: 4).",
    )

    p.add_argument(
        "--show-transformed",
        action="store_true",
        help="When the error is from Python stage, print the transformed code to stderr.",
    )

    return p


def _parse_indent_width(s: str) -> int:
    try:
        w = int(s)
        if w < 0:
            raise ValueError
        return w
    except ValueError:
        raise argparse.ArgumentTypeError("--indent must be a non-negative integer")


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    try:
        args = p.parse_args(argv)
    except SystemExit as e:
        # argparse używa kodu 2 dla złych flag; trzymajmy to jako "usage error"
        return 2 if e.code != 0 else 0

    # indent parsing -> usage error => 2
    try:
        indent_width = _parse_indent_width(args.indent)
    except argparse.ArgumentTypeError as e:
        print(f"typan-check: {e}", file=sys.stderr)
        return 2

    indent = " " * indent_width

    # read input -> IO error => 2
    if args.input == "-":
        try:
            src = sys.stdin.read()
        except Exception as e:
            print(f"typan-check: failed to read stdin: {e}", file=sys.stderr)
            return 2
        display_name = "<stdin>"
    else:
        path = Path(args.input)
        if not path.exists():
            print(f"typan-check: input file not found: {path}", file=sys.stderr)
            return 2
        if not path.is_file():
            print(f"typan-check: input is not a file: {path}", file=sys.stderr)
            return 2
        try:
            src = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"typan-check: failed to read file: {path}: {e}", file=sys.stderr)
            return 2
        display_name = str(path)

    ok, diags, transformed = check_text(src, indent=indent)

    if ok:
        return 0

    # syntax error => 1
    d = diags[0]

    if d.stage == "preprocess":
        # preprocess_text zwykle już ma ładnie sformatowany komunikat (format_error)
        print(d.message, file=sys.stderr)
        return 1

    # python stage
    loc = ""
    if d.lineno is not None and d.col is not None:
        loc = f"(line {d.lineno}, col {d.col}) "

    print(f"Python syntax error {loc}{d.message}", file=sys.stderr)

    if args.show_transformed and transformed is not None:
        print("\n--- transformed ---", file=sys.stderr)
        print(transformed, file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
