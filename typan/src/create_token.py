from typing import Tuple

__all__ = [
    "T_NEWLINE", "T_IDENT", "T_LBRACE", "T_RBRACE",
    "T_LPAREN", "T_RPAREN", "T_LBRACK", "T_RBRACK",
    "T_STRING", "T_COMMENT", "T_OTHER", "T_WS",
    "create_token",
]

T_NEWLINE = 1
T_IDENT   = 2
T_LBRACE  = 3
T_RBRACE  = 4
T_LPAREN  = 5
T_RPAREN  = 6
T_LBRACK  = 7
T_RBRACK  = 8
T_STRING  = 9
T_COMMENT = 10
T_OTHER   = 11
T_WS = 12

def create_token(kind, value, line, col) -> Tuple[int, str | None, int, int]:
    return (kind, value, line, col)
