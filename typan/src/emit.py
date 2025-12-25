# emit.py
from transform import E_LINE, E_OPEN, E_CLOSE, E_BLANK
from create_token import T_STRING, T_COMMENT, T_WS

def _open_line_to_str(tokens):
    n = len(tokens)
    comment_i = None
    for i, (kind, value, *_rest) in enumerate(tokens):
        if kind == T_COMMENT:
            comment_i = i
            break

    if comment_i is None:
        code = tokens
        tail = []
    else:
        code = tokens[:comment_i]
        tail = tokens[comment_i:]

    j = len(code)
    while j > 0 and code[j - 1][0] == T_WS:
        j -= 1
    code = code[:j]

    out = []
    for kind, value, *_ in code:
        if value is not None:
            out.append(value)

    out.append(":")

    for kind, value, *_ in tail:
        if value is not None:
            out.append(value)

    return "".join(out).rstrip()

def _line_to_str(tokens):
    out = []
    for kind, value, *_ in tokens:
        if value is None:
            continue
        out.append(value)
    return "".join(out)

def emit(events, indent_str="    "):
    indent = 0
    parts = []

    for kind, payload in events:
        if kind == E_BLANK:
            parts.append("\n")
            continue

        if kind == E_CLOSE:
            indent = max(0, indent - 1)
            continue

        if kind == E_OPEN:
            line = _open_line_to_str(payload)
            parts.append((indent_str * indent) + line + "\n")
            indent += 1
            continue

        if kind == E_LINE:
            line = _line_to_str(payload).rstrip()
            parts.append((indent_str * indent) + line + "\n")
            continue

    return "".join(parts)
