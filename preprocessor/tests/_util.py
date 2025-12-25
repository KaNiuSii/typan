# tests/_util.py
from __future__ import annotations

from preprocess import preprocess_text

def run(code: str, indent: int = 4) -> str:
    return preprocess_text(code, indent=" " * indent)

def norm(s: str) -> str:
    # normalizacja końców linii do '\n'
    return s.replace("\r\n", "\n").replace("\r", "\n")

def assert_out(got: str, expected: str):
    got_n = norm(got)
    exp_n = norm(expected)
    assert got_n == exp_n, f"\n--- GOT ---\n{got_n}\n--- EXP ---\n{exp_n}\n"
