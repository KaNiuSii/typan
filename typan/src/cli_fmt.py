from __future__ import annotations

import argparse
import sys
from pathlib import Path

from formatter import format_in_place, format_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="typan-fmt",
        description="typan-fmt: format brace-python (typan) after validating syntax (typan-check).",
    )

    p.add_argument("input", help="Input file path (brace syntax). Use '-' to read from stdin.")

    p.add_argument(
        "-o", "--output",
        help="Output file path. If omitted and --in-place not set, prints to stdout.",
        default=None,
    )

    p.add_argument("--in-place", action="store_true", help="Overwrite input file with formatted output.")
    p.add_argument("--check", action="store_true", help="Do not write. Exit 0 if already formatted, 1 if would change.")
    p.add_argument("--indent", default="4", help="Indent width in spaces (default: 4).")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # indent parsing -> usage error => 2
    try:
        w = int(args.indent)
        if w < 0:
            raise ValueError
    except ValueError:
        print("typan-fmt: --indent must be a non-negative integer", file=sys.stderr)
        return 2
    indent = " " * w

    # stdin mode
    if args.input == "-":
        if args.in_place:
            print("typan-fmt: cannot use --in-place with stdin", file=sys.stderr)
            return 2
        if args.check:
            print("typan-fmt: cannot use --check with stdin", file=sys.stderr)
            return 2

        src = sys.stdin.read()
        try:
            out = format_text(src, indent=indent)
        except SyntaxError as e:
            print(str(e), file=sys.stderr)
            return 1

        if args.output:
            Path(args.output).write_text(out, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(out)
        return 0

    # file mode
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"typan-fmt: input file not found: {in_path}", file=sys.stderr)
        return 2
    if not in_path.is_file():
        print(f"typan-fmt: input is not a file: {in_path}", file=sys.stderr)
        return 2

    if args.in_place:
        try:
            changed = format_in_place(str(in_path), indent=indent, check_only=args.check)
        except SyntaxError as e:
            print(str(e), file=sys.stderr)
            return 1

        if args.check:
            return 1 if changed else 0
        return 0

    # not in-place: output to file or stdout
    try:
        src = in_path.read_text(encoding="utf-8")
        out = format_text(src, indent=indent)
    except SyntaxError as e:
        print(str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print(f"typan-fmt: failed to read file: {in_path}: {e}", file=sys.stderr)
        return 2

    if args.output:
        try:
            Path(args.output).write_text(out, encoding="utf-8", newline="\n")
        except OSError as e:
            print(f"typan-fmt: failed to write output: {args.output}: {e}", file=sys.stderr)
            return 2
        return 0

    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
