from typing import Iterator, Tuple
from create_token import *

_STRING_PREFIX_CHARS = set("rRbBuUfF")

def _is_prefix_char(ch: str) -> bool:
    return ch in _STRING_PREFIX_CHARS

def _scan_string(text: str, i: int):
    """
    Scan a Python-like string starting at position i.
    Supports prefixes (r, f, b, u and combos) and single/double + triple quotes.

    Returns: (end_index, literal_text)
      - end_index points to first char AFTER the string literal
      - literal_text is text[i:end_index]
    Raises SyntaxError if unterminated.
    """
    n = len(text)

    # 1) prefixes
    j = i
    while j < n and _is_prefix_char(text[j]):
        j += 1

    if j >= n or text[j] not in ("'", '"'):
        return None  # not a string

    quote = text[j]
    # triple?
    is_triple = (j + 2 < n and text[j+1] == quote and text[j+2] == quote)

    if is_triple:
        delim = quote * 3
        k = j + 3
        while k + 2 < n:
            if text[k] == quote and text[k+1] == quote and text[k+2] == quote:
                k += 3
                return k, text[i:k]
            k += 1
        raise SyntaxError("Unterminated triple-quoted string")
    else:
        k = j + 1
        # treat raw strings a bit: if any 'r'/'R' in prefix, backslash doesn't escape quote
        prefix = text[i:j].lower()
        is_raw = "r" in prefix

        escaped = False
        while k < n:
            c = text[k]
            if c == "\n":
                # single-quoted strings cannot cross newline
                raise SyntaxError("Unterminated string literal (newline in single-quoted string)")
            if not is_raw:
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == quote:
                    k += 1
                    return k, text[i:k]
            else:
                if c == quote:
                    k += 1
                    return k, text[i:k]
            k += 1
        raise SyntaxError("Unterminated string literal")

def lex(text: str) -> Iterator[Tuple[int, str | None, int, int]]:
    i = 0
    line = 1
    col = 1
    n = len(text)

    while i < n:
        ch = text[i]

        # NEWLINE
        if ch == "\n":
            yield create_token(T_NEWLINE, None, line, col)
            i += 1
            line += 1
            col = 1
            continue

        # STRING
        if _is_prefix_char(ch) or ch in ("'", '"'):
            scanned = _scan_string(text, i)
            if scanned is not None:
                end, literal = scanned
                start_col = col
                # update line/col based on literal content
                nl_count = literal.count("\n")
                if nl_count == 0:
                    yield create_token(T_STRING, literal, line, start_col)
                    col += (end - i)
                    i = end
                else:
                    yield create_token(T_STRING, literal, line, start_col)
                    # compute last line length after last '\n'
                    last_nl = literal.rfind("\n")
                    line += nl_count
                    col = (len(literal) - last_nl)
                    i = end
                continue

        # WHITESPACE
        if ch in " \t\r":
            start_col = col
            j = i + 1
            while j < n and text[j] in " \t\r":
                j += 1
            yield create_token(T_WS, text[i:j], line, start_col)
            col += (j - i)
            i = j
            continue

        # COMMENT
        if ch == "#":
            start_col = col
            j = i
            while j < n and text[j] != "\n":
                j += 1
            value = text[i:j]
            yield create_token(T_COMMENT, value, line, start_col)
            col += (j - i)
            i = j
            continue

        # STRING (single or double-quoted)
        if ch == "'" or ch == '"':
            quote = ch
            start_col = col
            j = i + 1
            escaped = False

            while j < n:
                c = text[j]
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == quote:
                    j += 1
                    break
                j += 1

            value = text[i:j]
            yield create_token(T_STRING, value, line, start_col)
            col += (j - i)
            i = j
            continue

        # IDENT (to fix "ifx" problem)
        if ch.isalpha() or ch == "_":
            start_col = col
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            yield create_token(T_IDENT, text[i:j], line, start_col)
            col += (j - i)
            i = j
            continue

        # BRACES / PARENS / BRACKETS
        if ch == "{":
            yield create_token(T_LBRACE, ch, line, col)
        elif ch == "}":
            yield create_token(T_RBRACE, ch, line, col)
        elif ch == "(":
            yield create_token(T_LPAREN, ch, line, col)
        elif ch == ")":
            yield create_token(T_RPAREN, ch, line, col)
        elif ch == "[":
            yield create_token(T_LBRACK, ch, line, col)
        elif ch == "]":
            yield create_token(T_RBRACK, ch, line, col)
        else:
            # IDENT / OTHER (na razie wszystko jako OTHER)
            yield create_token(T_OTHER, ch, line, col)

        i += 1
        col += 1