# tests/test_e2e.py
from __future__ import annotations

import pytest
from tests._util import run, assert_out


def test_basic_if():
    code = """\
if x {
print("{")
}
"""
    expected = """\
if x:
    print("{")
"""
    assert_out(run(code), expected)


def test_if_else_same_line():
    code = """\
if x {
a = 1
} else {
a = 2
}
"""
    expected = """\
if x:
    a = 1
else:
    a = 2
"""
    assert_out(run(code), expected)


def test_if_elif_else_chain_same_line():
    code = """\
if x {
a = 1
} elif y {
a = 2
} elif z {
a = 3
} else {
a = 4
}
"""
    expected = """\
if x:
    a = 1
elif y:
    a = 2
elif z:
    a = 3
else:
    a = 4
"""
    assert_out(run(code), expected)


def test_multiple_closes_before_else():
    code = """\
if a {
if b {
c = 1
}
} else {
c = 2
}
"""
    expected = """\
if a:
    if b:
        c = 1
else:
    c = 2
"""
    assert_out(run(code), expected)


def test_empty_block_inserts_pass():
    code = """\
if x {
}
"""
    expected = """\
if x:
    pass
"""
    assert_out(run(code), expected)


def test_nested_empty_blocks_pass_only_inner():
    code = """\
if x {
if y {
}
} else {
}
"""
    expected = """\
if x:
    if y:
        pass
else:
    pass
"""
    assert_out(run(code), expected)


def test_for_while_def_class_with():
    code = """\
class A {
def f(self, xs) {
for x in xs {
if x {
print(x)
}
}
while False {
}
with open("a.txt") as f {
pass
}
}
}
"""
    expected = """\
class A:
    def f(self, xs):
        for x in xs:
            if x:
                print(x)
        while False:
            pass
        with open("a.txt") as f:
            pass
"""
    assert_out(run(code), expected)


def test_async_headers():
    code = """\
async def f() {
async for x in xs {
await g(x)
}
async with lock {
pass
}
}
"""
    expected = """\
async def f():
    async for x in xs:
        await g(x)
    async with lock:
        pass
"""
    assert_out(run(code), expected)


def test_try_except_finally_chain():
    code = """\
try {
a = 1
} except Exception as e {
} finally {
}
"""
    out = run(code)
    assert "try:" in out
    assert "except Exception as e:" in out
    assert "finally:" in out
    assert "pass" in out

import pytest

def test_try_except_finally_unmatched_brace_errors():
    code = """\
try {
a = 1
} except Exception as e {
}
} finally {
}
"""
    with pytest.raises(SyntaxError):
        run(code)


def test_match_case_basic():
    code = """\
match x {
case 1 {
y = 10
}
case _ {
y = 0
}
}
"""
    expected = """\
match x:
    case 1:
        y = 10
    case _:
        y = 0
"""
    assert_out(run(code), expected)


def test_parens_logical_lines_header_multiline():
    code = """\
if (
a
and b
) {
x = 1
}
"""
    expected = """\
if (
a
and b
):
    x = 1
"""
    # To zostawia newline’y w środku warunku (bo WS/newline zachowujesz w stringu?),
    # ale ważne: ':' i indent muszą być prawidłowe.
    out = run(code)
    assert out.strip().endswith("x = 1")
    assert "):\n    x = 1" in out


def test_braces_inside_dict_literal_do_not_open_blocks():
    code = """\
if x {
d = {"a": 1, "b": {1, 2, 3}}
}
"""
    expected = """\
if x:
    d = {"a": 1, "b": {1, 2, 3}}
"""
    assert_out(run(code), expected)


def test_braces_in_string_do_not_affect_blocks():
    code = """\
if x {
s = "{ not a block }"
}
"""
    expected = """\
if x:
    s = "{ not a block }"
"""
    assert_out(run(code), expected)


def test_triple_quote_string_with_braces_and_newlines():
    # To przejdzie dopiero po dodaniu triple-quote skanera w lexerze
    code = '''\
if x {
s = """hello {
world
} still string"""
}
'''
    out = run(code)
    assert "if x:" in out
    assert '"""hello {' in out
    assert "still string" in out


def test_comment_preservation_and_trailing_comment_on_opener():
    code = """\
if x { # comment
# inside
}
"""
    out = run(code)
    assert "if x:" in out
    assert "# comment" in out
    assert "# inside" in out


def test_unmatched_closing_brace_error_has_location():
    code = """\
}
"""
    with pytest.raises(SyntaxError) as e:
        run(code)
    msg = str(e.value)
    assert "Unmatched" in msg
    assert "line" in msg


def test_missing_closing_brace_error_has_location():
    code = """\
if x {
a = 1
"""
    with pytest.raises(SyntaxError) as e:
        run(code)
    msg = str(e.value)
    assert "Missing closing" in msg
    assert "line" in msg

def test_dict_literal_simple():
    code = """\
if x {
d = {"a": 1, "b": 2}
}
"""
    expected = """\
if x:
    d = {"a": 1, "b": 2}
"""
    assert_out(run(code), expected)

def test_dict_literal_nested():
    code = """\
if x {
d = {
    "a": {"x": 1},
    "b": {"y": 2},
}
}
"""
    out = run(code)
    assert "if x:" in out
    assert 'd = {' in out
    assert '"a": {"x": 1}' in out
    assert '"b": {"y": 2}' in out

def test_dict_literal_as_function_argument():
    code = """\
if x {
foo({
    "a": 1,
    "b": 2,
})
}
"""
    out = run(code)
    assert "if x:" in out
    assert "foo({" in out
    assert '"a": 1' in out
    assert '"b": 2' in out

def test_dict_with_braces_in_strings():
    code = """\
if x {
d = {
    "a": "{ not a block }",
    "b": "still { string }",
}
}
"""
    out = run(code)
    assert "if x:" in out
    assert 'd = {' in out
    assert '"a": "{ not a block }"' in out
    assert '"b": "still { string }"' in out

def test_dict_comprehension():
    code = """\
if x {
d = {k: v for k, v in items}
}
"""
    expected = """\
if x:
    d = {k: v for k, v in items}
"""
    assert_out(run(code), expected)

def test_dict_on_same_line_as_opener():
    code = """\
if x { d = {"a": 1} }
"""
    expected = """\
if x:
    d = {"a": 1}
"""
    assert_out(run(code), expected)

def test_dict_does_not_affect_brace_stack():
    code = """\
if x {
a = 1
d = {"a": 1}
b = 2
}
"""
    expected = """\
if x:
    a = 1
    d = {"a": 1}
    b = 2
"""
    assert_out(run(code), expected)

def test_inline_if_else_one_line_is_rejected():
    code = "if x { a = 1 } else { a = 2 }\n"
    with pytest.raises(SyntaxError):
        run(code)


def test_inline_block_header_comment():
    code = """\
if x { a = 1 }  # tail
"""
    out = run(code)
    assert "if x:" in out
    assert "a = 1" in out
    assert "# tail" in out

def test_inline_empty_block_inserts_pass():
    code = "if x { }\n"
    expected = "if x:\n    pass\n"
    assert_out(run(code), expected)

def test_set_literal_does_not_close_block():
    code = """\
if x {
s = {1, 2, 3}
print(s)
}
"""
    expected = """\
if x:
    s = {1, 2, 3}
    print(s)
"""
    assert_out(run(code), expected)

def test_dict_of_sets_literal():
    code = """\
if x {
d = {"a": {1,2}, "b": {3,4}}
}
"""
    expected = """\
if x:
    d = {"a": {1,2}, "b": {3,4}}
"""
    assert_out(run(code), expected)

def test_raw_string_with_braces():
    code = r"""\
if x {
s = r"\{ \} \\"
}
"""
    out = run(code)
    assert "if x:" in out
    assert r's = r"\{ \} \\"' in out or r's = r"\{ \} \\\\"' in out

def test_fstring_braces_not_blocks():
    code = """\
if x {
s = f"val={{ {1} }}"
}
"""
    out = run(code)
    assert "if x:" in out
    assert 'f"val=' in out

def test_triple_raw_string():
    code = r'''\
if x {
s = r"""a
{ b }
c"""
}
'''
    out = run(code)
    assert "if x:" in out
    assert 'r"""a' in out

def test_else_line_with_comment_after_brace():
    code = """\
if x {
a = 1
} else { # c
a = 2
}
"""
    out = run(code)
    assert "else:" in out
    assert "# c" in out

def test_empty_block_with_only_comment_still_pass():
    code = """\
if x {
# just comment
}
"""
    out = run(code)
    assert "pass" in out

def test_multiline_opener_not_inline_error():
    code = "if x {\nprint(1)\n}\n"
    expected = "if x:\n    print(1)\n"
    assert_out(run(code), expected)
