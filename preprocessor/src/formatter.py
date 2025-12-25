from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

from lex import lex
from lines import logical_lines
from create_token import T_IDENT, T_LBRACE, T_RBRACE, T_WS, T_COMMENT, T_STRING
from check_text import check_text


# event kinds
E_LINE = "LINE"
E_OPEN = "OPEN"
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

def _normalize_ws_between_tokens(tokens):
    """
    Zamienia wiele WS między tokenami na pojedynczą spację.
    NIE rusza stringów ani komentarzy.
    """
    out = []
    prev_was_space = False

    for kind, value, *rest in tokens:
        if kind == T_WS:
            if not prev_was_space:
                out.append((kind, " ", *rest))
                prev_was_space = True
            continue

        # string / comment – resetuj stan, zachowaj 1:1
        out.append((kind, value, *rest))
        prev_was_space = False

    return out

def _strip_trailing_ws(tokens):
    j = len(tokens)
    while j > 0 and tokens[j - 1][0] == T_WS:
        j -= 1
    return tokens[:j], tokens[j:]


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


def _is_block_opener(tokens) -> bool:
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


def _line_has_code(tokens) -> bool:
    for k, _v, *_ in tokens:
        if k in (T_WS,):
            continue
        # komentarz traktujemy jako "coś", żeby linia komentarza się zachowała
        if k == T_COMMENT:
            return True
        return True
    return False


def _update_literal_depth(tokens, depth: int) -> int:
    """
    Track '{' '}' that are NOT block braces (dict/set/comprehension).
    Tu to jest heurystyka jak w preprocess: gdy jesteśmy wewnątrz literału,
    nie traktujemy '}' na początku linii jako zamknięcia bloku.
    """
    for kind, _value, *_ in tokens:
        if kind == T_LBRACE:
            depth += 1
        elif kind == T_RBRACE:
            depth = max(0, depth - 1)
    return depth


def _find_matching_rbrace_inline(tokens, start_idx: int) -> Optional[int]:
    """
    Find matching '}' for a BLOCK '{' at tokens[start_idx], but only in SAME logical line.
    Braces inside the inline body are treated as literal braces.
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


def _tokens_to_text(tokens) -> str:
    return "".join(v for _k, v, *_ in tokens)


def _format_line_text(tokens) -> str:
    tokens = _strip_leading_ws(tokens)
    tokens = _normalize_ws_between_tokens(tokens)
    core, _ = _strip_trailing_ws(tokens)
    return _tokens_to_text(core).rstrip()


def _format_open_header(tokens) -> str:
    """
    Z linii typu:  if x {   # comment
    robi:          if x { # comment
    (bez indentu; indent dodaje emitter)
    """
    tokens = _strip_leading_ws(tokens)
    tokens = _normalize_ws_between_tokens(tokens)
    core, tail = _strip_trailing_ws_comment(tokens)

    # core kończy się '{'
    # bierzemy tekst przed '{'
    before = core[:-1]
    before_text = _tokens_to_text(_strip_trailing_ws(before)[0]).rstrip()

    # tail może zawierać komentarz i WS – normalizujemy:
    tail_text = _tokens_to_text(tail).strip()
    if tail_text:
        # zwykle "# ..."
        return f"{before_text} {{ {tail_text} }}"
    return f"{before_text} {{"

def _format_close_trailing(tokens) -> str:
    """
    Zwraca trailing tylko jeśli po '}' jest komentarz.
    Jeśli po '}' jest kod (np. 'else {'), to trailing MUSI być puste,
    żeby formatter mógł rozbić to na osobne linie.
    """
    t = _strip_leading_ws(tokens)
    if not t or t[0][0] != T_RBRACE:
        return ""

    rest = _strip_leading_ws(t[1:])
    if not rest:
        return ""

    if rest[0][0] == T_COMMENT:
        return _tokens_to_text(rest).strip()

    return ""



def format_events_from_text(src: str) -> Iterator[tuple[str, object]]:
    """
    Produkuje eventy (OPEN/CLOSE/LINE/BLANK) dla formattera.
    Ważne: NIE wstawia 'pass' dla pustych bloków (formatter nie zmienia semantyki).
    Rozbija konstrukcje w stylu: '} else {' na osobne eventy.
    Rozwija inline: 'if x { stmt }' do multiline z { }.
    """
    tokens = lex(src)
    lines = logical_lines(tokens)

    stack: list[object] = []
    literal_depth = 0

    for line_tokens in lines:
        if line_tokens == []:
            yield (E_BLANK, None)
            continue

        tokens_line = line_tokens

        # 1) leading '}' zamyka blok (jeśli nie jesteśmy w literałach)
        while True:
            t = _strip_leading_ws(tokens_line)
            if t and t[0][0] == T_RBRACE and literal_depth == 0:
                if not stack:
                    # syntax should be caught earlier by checker, but keep safe
                    yield (E_CLOSE, t)  # fallback
                    tokens_line = t[1:]
                else:
                    stack.pop()
                    # close with possible trailing comment (but not '} else {')
                    yield (E_CLOSE, t)
                    tokens_line = t[1:]
                if not tokens_line:
                    break
                continue
            break

        tokens_line = _strip_leading_ws(tokens_line)
        if not tokens_line:
            continue

        # 2) inline block: if x { stmt }
        idx_lbrace = None
        idx_rbrace = None

        for i, tok in enumerate(tokens_line):
            if tok[0] != T_LBRACE:
                continue
            if _is_block_opener(tokens_line[: i + 1]):
                j = _find_matching_rbrace_inline(tokens_line, i)
                if j is not None:
                    idx_lbrace = i
                    idx_rbrace = j
                break

        if idx_lbrace is not None and idx_rbrace is not None:
            # emit OPEN
            opener_tokens = tokens_line[: idx_lbrace + 1]
            yield (E_OPEN, opener_tokens)
            stack.append("{")

            # body as LINE (if any)
            body = _strip_leading_ws(tokens_line[idx_lbrace + 1 : idx_rbrace])
            if body and _line_has_code(body):
                yield (E_LINE, body)

            # emit CLOSE
            close_tok = tokens_line[idx_rbrace : idx_rbrace + 1]
            yield (E_CLOSE, close_tok)
            stack.pop()

            # remainder after inline close (formatter rozbije dalej jeśli trzeba)
            tokens_line = _strip_leading_ws(tokens_line[idx_rbrace + 1 :])
            if not tokens_line:
                continue

        # 3) normal opener
        if _is_block_opener(tokens_line):
            yield (E_OPEN, tokens_line)
            stack.append("{")
            continue

        # 4) normal line
        literal_depth = _update_literal_depth(tokens_line, literal_depth)
        yield (E_LINE, tokens_line)

    # brakujące } powinny być złapane przez checker, ale dla pewności:
    if stack:
        # nic nie emitujemy; to błąd składni, ale do formattera i tak nie dojdziemy,
        # bo check_text ma być odpalony wcześniej.
        pass


def emit_pretty(events: Iterable[tuple[str, object]], *, indent: str = "    ") -> str:
    """
    Emitter dla typan (formatowanie brace-syntax).
    Zasady:
      - OPEN: header w jednej linii + '{'
      - CLOSE: '}' w jednej linii
      - LINE: trim leading/trailing, wstaw indent wg poziomu
      - BLANK: maks 1 pusta linia pod rząd
    """
    out: list[str] = []
    level = 0
    blank_pending = False

    for kind, payload in events:
        if kind == E_BLANK:
            blank_pending = True
            continue

        if blank_pending:
            # maks 1 pusta linia
            if out and out[-1] != "":
                out.append("")
            blank_pending = False

        if kind == E_OPEN:
            line = _format_open_header(payload)  # type: ignore[arg-type]
            out.append(f"{indent * level}{line}")
            level += 1
            continue

        if kind == E_CLOSE:
            # payload może być: sam token '}' albo '}' + trailing
            level = max(0, level - 1)
            # jeśli payload to lista tokenów, pierwszy to '}'
            trailing = _format_close_trailing(payload)  # type: ignore[arg-type]
            if trailing:
                out.append(f"{indent * level}}} {trailing}")
            else:
                out.append(f"{indent * level}}}")
            continue

        if kind == E_LINE:
            txt = _format_line_text(payload)  # type: ignore[arg-type]
            if txt == "":
                # traktuj jako blank, ale nadal ogranicz do 1
                if out and out[-1] != "":
                    out.append("")
                continue
            out.append(f"{indent * level}{txt}")
            continue

        # unknown event: ignore

    # newline na końcu pliku
    return "\n".join(out).rstrip() + "\n"


def format_text(src: str, *, indent: str = "    ") -> str:
    """
    Najpierw check (preprocess+compile). Jeśli OK -> format.
    Jeśli nie OK -> rzuca SyntaxError z komunikatem jak typan-check.
    """
    ok, diags, _transformed = check_text(src, indent=indent)
    if not ok:
        d = diags[0]
        raise SyntaxError(d.message)

    events = format_events_from_text(src)
    return emit_pretty(events, indent=indent)


def format_file(in_path: str, out_path: str, *, indent: str = "    ") -> None:
    import pathlib
    src = pathlib.Path(in_path).read_text(encoding="utf-8")
    out = format_text(src, indent=indent)
    pathlib.Path(out_path).write_text(out, encoding="utf-8", newline="\n")


def format_in_place(path: str, *, indent: str = "    ", check_only: bool = False) -> bool:
    import pathlib
    p = pathlib.Path(path)
    src = p.read_text(encoding="utf-8")

    out = format_text(src, indent=indent)
    changed = (out != src)

    if check_only:
        return changed

    if changed:
        p.write_text(out, encoding="utf-8", newline="\n")
    return changed
