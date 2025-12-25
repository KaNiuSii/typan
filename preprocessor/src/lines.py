from create_token import (
    T_NEWLINE, T_LPAREN, T_RPAREN, T_LBRACK, T_RBRACK,
)

def logical_lines(tokens):
    """
    Group tokens into logical lines.
    Newline ends a line only when we're not inside () or [].

    Yields: list[token]
    """
    paren = 0
    brack = 0
    buf = []

    for tok in tokens:
        kind, value, line, col = tok

        if kind == T_LPAREN:
            paren += 1
            buf.append(tok)
            continue

        if kind == T_RPAREN:
            if paren > 0:
                paren -= 1
            buf.append(tok)
            continue

        if kind == T_LBRACK:
            brack += 1
            buf.append(tok)
            continue

        if kind == T_RBRACK:
            if brack > 0:
                brack -= 1
            buf.append(tok)
            continue

        if kind == T_NEWLINE:
            # NEWLINE kończy logical line tylko jeśli nie jesteśmy w () lub []
            if paren == 0 and brack == 0:
                if buf:
                    yield buf
                    buf = []
                else:
                    # pusta linia -> emituj pustą (przyda się w emitterze)
                    yield []
            else:
                # newline wewnątrz nawiasów jest ignorowany (ale możesz zachować, jeśli chcesz)
                # buf.append(tok)  # opcjonalnie
                pass
            continue

        buf.append(tok)

    # jeśli coś zostało bez newline na końcu pliku
    if buf:
        yield buf