from __future__ import annotations

import argparse
import sys
from pathlib import Path

from check_text import check_text
from preprocess import preprocess_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="typan",
        description="typan: preprocess brace-block Python into real Python (adds ':' + indentation).",
    )

    p.add_argument(
        "input",
        help="Input file path (brace syntax). Use '-' to read from stdin.",
    )

    p.add_argument(
        "-o",
        "--output",
        help="Output file path. If omitted and --in-place not set, prints to stdout.",
        default=None,
    )

    p.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite input file with processed output.",
    )

    p.add_argument(
        "--check",
        action="store_true",
        help="Do not write. Exit code 0 if no changes needed, 1 if file would change.",
    )

    p.add_argument(
        "--indent",
        default="4",
        help="Indent width in spaces (default: 4).",
    )

    p.add_argument(
        "--validate",
        action="store_true",
        help="Run typan-check validation (preprocess + Python compile) before writing output.",
    )

    p.add_argument(
        "--show-transformed",
        action="store_true",
        help="When validation fails at Python stage, print transformed code to stderr.",
    )

    return p


def _print_validation_failure(diags, show_transformed: bool, transformed: str | None) -> int:
    d = diags[0]

    if d.stage == "preprocess":
        print(d.message, file=sys.stderr)
        return 1

    loc = ""
    if d.lineno is not None and d.col is not None:
        loc = f"(line {d.lineno}, col {d.col}) "

    print(f"Python syntax error {loc}{d.message}", file=sys.stderr)

    if show_transformed and transformed is not None:
        print("\n--- transformed ---", file=sys.stderr)
        print(transformed, file=sys.stderr)

    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # parse indent
    try:
        indent_width = int(args.indent)
        if indent_width < 0:
            raise ValueError
    except ValueError:
        print("typan: --indent must be a non-negative integer", file=sys.stderr)
        return 2

    indent = " " * indent_width

    # stdin mode
    if args.input == "-":
        if args.in_place:
            print("typan: cannot use --in-place with stdin", file=sys.stderr)
            return 2

        try:
            src = sys.stdin.read()
        except Exception as e:
            print(f"typan: failed to read stdin: {e}", file=sys.stderr)
            return 2

        # optional validate (runs full typan-check pipeline)
        if args.validate:
            ok, diags, transformed = check_text(src, indent=indent)
            if not ok:
                return _print_validation_failure(diags, args.show_transformed, transformed)

        out = preprocess_text(src, indent=indent)

        if args.check:
            # stdin: nie ma sensu "czy by się zmieniło", bo nie mamy z czym porównać
            print("typan: cannot use --check with stdin", file=sys.stderr)
            return 2

        if args.output:
            try:
                Path(args.output).write_text(out, encoding="utf-8", newline="\n")
            except Exception as e:
                print(f"typan: failed to write output file: {args.output}: {e}", file=sys.stderr)
                return 2
        else:
            sys.stdout.write(out)

        return 0

    # file mode
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"typan: input file not found: {in_path}", file=sys.stderr)
        return 2
    if not in_path.is_file():
        print(f"typan: input is not a file: {in_path}", file=sys.stderr)
        return 2

    try:
        src = in_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"typan: failed to read file: {in_path}: {e}", file=sys.stderr)
        return 2

    # optional validate (runs full typan-check pipeline)
    if args.validate:
        ok, diags, transformed = check_text(src, indent=indent)
        if not ok:
            return _print_validation_failure(diags, args.show_transformed, transformed)

    # transform
    out = preprocess_text(src, indent=indent)

    # --check (diff)
    if args.check:
        return 1 if out != src else 0

    # --in-place
    if args.in_place:
        try:
            in_path.write_text(out, encoding="utf-8", newline="\n")
        except Exception as e:
            print(f"typan: failed to write file in-place: {in_path}: {e}", file=sys.stderr)
            return 2
        return 0

    # --output
    if args.output:
        out_path = Path(args.output)
        try:
            out_path.write_text(out, encoding="utf-8", newline="\n")
        except Exception as e:
            print(f"typan: failed to write output file: {out_path}: {e}", file=sys.stderr)
            return 2
        return 0

    # default: stdout
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
