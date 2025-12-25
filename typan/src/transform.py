# transform.py
from create_token import (
    T_IDENT, T_LBRACE, T_RBRACE, T_WS, T_COMMENT
)

# event kinds
E_LINE  = "LINE"
E_OPEN  = "OPEN"
E_CLOSE = "CLOSE"
E_BLANK = "BLANK"

BLOCK_HEADS = {
    "if", "elif", "else",
    "for", "while",
    "def", "class",
    "try", "except", "finally",
    "with",
    "match", "case",
}

def _strip_trailing_ws_comment(tokens):
    j = len(tokens)
    while j > 0 and tokens[j - 1][0] in (T_WS, T_COMMENT):
        j -= 1
    return tokens[:j], tokens[j:]

def _strip_leading_ws(tokens):
    i = 0
    n = len(tokens)
    while i < n and tokens[i][0] == T_WS:
        i += 1
    return tokens[i:]

def _first_ident(tokens):
    for kind, value, *_ in tokens:
        if kind == T_IDENT:
            return value
    return None

def _second_ident(tokens):
    seen = 0
    for kind, value, *_ in tokens:
        if kind == T_IDENT:
            seen += 1
            if seen == 2:
                return value
    return None

def _is_block_opener(tokens):
    """
    Block opener = logical line whose last non-(WS/COMMENT) token is '{'
    AND first ident is a block head keyword (or async def/for/with).
    """
    if not tokens:
        return False

    core, _tail = _strip_trailing_ws_comment(tokens)
    if not core:
        return False
    if core[-1][0] != T_LBRACE:
        return False

    head = core[:-1]
    first = _first_ident(head)
    if not first:
        return False

    if first == "async":
        second = _second_ident(head)
        return second in ("def", "for", "with")

    return first in BLOCK_HEADS

def _line_has_code(tokens):
    for k, v, *_ in tokens:
        if k == T_WS or k == T_COMMENT:
            continue
        return True
    return False

def _make_pass_token(ref_tok):
    _, _, ln, col = ref_tok
    return (T_IDENT, "pass", ln, col)

def _update_literal_depth(tokens, depth: int) -> int:
    """
    Track '{' '}' that are NOT block braces (dict/set/comprehension).
    Strings don't contain brace tokens (lexer emits them as T_STRING).
    """
    for kind, value, *_ in tokens:
        if kind == T_LBRACE:
            depth += 1
        elif kind == T_RBRACE:
            depth = max(0, depth - 1)
    return depth

def _find_matching_rbrace_inline(tokens, start_idx):
    """
    Find the matching '}' for a BLOCK '{' at tokens[start_idx],
    but only within the SAME logical line.
    Braces inside the inline body are treated as literal (dict/set) braces.
    """
    literal_depth = 0
    i = start_idx + 1
    n = len(tokens)

    while i < n:
        k = tokens[i][0]
        if k == T_LBRACE:
            literal_depth += 1
        elif k == T_RBRACE:
            if literal_depth > 0:
                literal_depth -= 1
            else:
                return i
        i += 1

    return None

def transform(lines):
    """
    Features:
      - supports constructs like '} else {' on the same logical line
      - inserts 'pass' for empty blocks
      - ignores dict/set braces via literal_depth (multiline dict won't close blocks)
      - inline single-statement blocks: `if x { stmt }`
        (only if the closing '}' is on the SAME logical line)
    """
    stack = []  # (open_lbrace_token, has_body_bool)
    literal_depth = 0

    for line_tokens in lines:
        if line_tokens == []:
            yield (E_BLANK, None)
            continue

        tokens = line_tokens

        # ------------------------------------------------------------
        # 1) Leading '}' closes a BLOCK only when not inside literal braces
        # ------------------------------------------------------------
        while True:
            t = _strip_leading_ws(tokens)
            if t and t[0][0] == T_RBRACE and literal_depth == 0:
                if not stack:
                    _, _, ln, col = t[0]
                    raise SyntaxError(f"Unmatched '}}' at line {ln}, col {col}")

                open_tok, has_body = stack.pop()
                if not has_body:
                    yield (E_LINE, [_make_pass_token(open_tok)])

                yield (E_CLOSE, t[0])

                tokens = t[1:]
                if not tokens:
                    break
                continue
            break

        tokens = _strip_leading_ws(tokens)
        if not tokens:
            continue

        # ------------------------------------------------------------
        # 2) INLINE BLOCK attempt:
        #    Only if we can find matching '}' on SAME logical line.
        # ------------------------------------------------------------
        idx_lbrace = None
        idx_rbrace = None

        for i, tok in enumerate(tokens):
            if tok[0] != T_LBRACE:
                continue
            if _is_block_opener(tokens[:i + 1]):
                j = _find_matching_rbrace_inline(tokens, i)
                if j is not None:
                    idx_lbrace = i
                    idx_rbrace = j
                break  # first block-opener '{' is what we care about

        if idx_lbrace is not None:
            # header: prefix up to '{' with trailing comment/WS preserved
            prefix = tokens[:idx_lbrace + 1]
            core, tail = _strip_trailing_ws_comment(prefix)  # core ends with '{'
            header = core[:-1] + tail
            open_tok = core[-1]

            # parent has body
            if stack:
                parent_open, _ = stack[-1]
                stack[-1] = (parent_open, True)

            # emit OPEN
            stack.append((open_tok, False))
            yield (E_OPEN, header)

            # inline body
            body = _strip_leading_ws(tokens[idx_lbrace + 1:idx_rbrace])
            if body and _line_has_code(body):
                ot, _ = stack[-1]
                stack[-1] = (ot, True)
                yield (E_LINE, body)

            # close inline block
            ot, has_body = stack.pop()
            if not has_body:
                yield (E_LINE, [_make_pass_token(ot)])
            yield (E_CLOSE, tokens[idx_rbrace])

            # continue with remainder after inline close (e.g. `else { ... }`)
            tokens = _strip_leading_ws(tokens[idx_rbrace + 1:])
            if not tokens:
                continue

            first = _first_ident(tokens)
            if first in ("else", "elif", "except", "finally"):
                _, _, ln, col = tokens[0]
                raise SyntaxError(
                    f"Inline '{first}' is not allowed; put '{first}' on a new line (line {ln}, col {col})"
                )

        # ------------------------------------------------------------
        # 3) Normal multiline block opener
        # ------------------------------------------------------------
        if _is_block_opener(tokens):
            core, tail = _strip_trailing_ws_comment(tokens)
            header = core[:-1] + tail
            open_tok = core[-1]

            if stack:
                parent_open, _ = stack[-1]
                stack[-1] = (parent_open, True)

            stack.append((open_tok, False))
            yield (E_OPEN, header)
            continue

        # ------------------------------------------------------------
        # 4) Normal line
        # ------------------------------------------------------------
        if stack and _line_has_code(tokens):
            open_tok, _ = stack[-1]
            stack[-1] = (open_tok, True)

        # update literal depth for non-opener lines
        literal_depth = _update_literal_depth(tokens, literal_depth)
        yield (E_LINE, tokens)

    if stack:
        open_tok, _ = stack[-1]
        _, _, ln, col = open_tok
        raise SyntaxError(f"Missing closing '}}' for block opened at line {ln}, col {col}")
