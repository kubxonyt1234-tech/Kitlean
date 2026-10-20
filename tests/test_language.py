import subprocess
import sys
from pathlib import Path

import pytest

from kitlean.errors import KitleanError
from kitlean.interpreter import Interpreter
from kitlean.lexer import Lexer
from kitlean.parser import Parser


def test_lexer_ast():
    source = '[create gui.menu="menu"]\n'
    assert any(t.value == "create" for t in Lexer(source).tokenize())
    assert Parser(source).parse()[0].kind == "create"


def test_objects_and_both_text_methods():
    i = Interpreter()
    r = i.execute(
        '[create gui.menu="menu"]\n[create item.button="a"]\na.text/"Pierwszy"\n[create item.button="b"]\ncreate item.button/"Drugi"'
    )
    assert r.get("a").properties["text"] == "Pierwszy"
    assert r.get("b").properties["text"] == "Drugi"
    assert r.get("a").parent == "menu"
    assert r.get("menu").properties["size"] == (800, 500)
    assert r.get("a").properties["size"] == (160, 45)


def test_context():
    r = Interpreter().execute(
        '[create gui.menu="a"]\n[create item.button="b"]\n[create gui.menu="c"]\n[create item.button="d"]\nb.parent/"a"\ncreate item.button/"A"'
    )
    assert r.get("b").properties["text"] == "A"
    assert r.get("d").properties["text"] == ""


def test_language():
    out = []
    i = Interpreter(output=lambda *x: out.append(x))
    i.execute("""var points = 10
if points >= 10:
    print("Wygrana!")
else:
    print("Nie")
repeat 3:
    points = points + 1
function welcome(name):
    print("Cześć " + name)
welcome("Kitlean")
var values = [true, false, null, 2]
print(points, values[0], values[2], 2 + 3 * 4, len(values))
if false and missing:
    print("Nie")
if false:
    print("Nie")
else:
    print("Else")
""")
    assert out == [
        ("Wygrana!",),
        ("Cześć Kitlean",),
        (13, True, None, 14, 4),
        ("Else",),
    ]


def test_event_state():
    out = []
    r = Interpreter(output=out.append).execute("""[create gui.menu="m"]
[create item.button="b"]
if b.clicked:
    print("click")
if b.hovered:
    print("hover")
""")
    r.events.emit(r.get("b"), "clicked")
    r.events.emit(r.get("b"), "hovered")
    r.set("b", "disabled", True)
    r.events.emit(r.get("b"), "clicked")
    r.set("b", "disabled", False)
    r.set("b", "visible", False)
    r.events.emit(r.get("b"), "hovered")
    assert out == ["click", "hover"]
    assert r.read("b", "visible") is False


@pytest.mark.parametrize(
    "source",
    [
        '[create item.button="b"]',
        '[create gui.menu="m"]\n[create gui.menu="m"]',
        'unknown.text/"x"',
        '[create gui.menu="m"]\nm.unknown/1',
        '[create gui.menu="m"]\nm.size/(0,10)',
        '[create gui.menu="m"]\nm.visible/"yes"',
        "repeat -1:\n    print(1)",
        "print(1 / 0)",
        "function f(x):\n    print(x)\nf()",
        "if true\n    print(1)",
        'print(__import__("os"))',
        "print((1).__class__)",
        "print([x for x in [1]])",
        "var x = {1: 2}",
        'create item.button/"x"',
    ],
)
def test_errors(source):
    with pytest.raises(KitleanError):
        Interpreter().execute(source)


def test_error_line():
    with pytest.raises(KitleanError) as info:
        Interpreter().execute('var x = 1\nunknown.text/"x"')
    assert info.value.line == 2
    assert "Hint:" in str(info.value)


@pytest.mark.parametrize(
    "args,code,expected",
    [
        (["--version"], 0, "Kitlean 0.4 Beta"),
        (["help"], 0, "usage:"),
        (["check", "examples/main_menu.kit"], 0, "Składnia poprawna"),
        (["run", "examples/hello.kit"], 0, "Hello Kitlean!"),
        (["run", "nonexistent.kit"], 1, "KitleanError"),
    ],
)
def test_cli(args, code, expected):
    result = subprocess.run(
        [sys.executable, "-m", "kitlean", *args],
        capture_output=True,
        cwd=Path(__file__).parents[1],
    )
    assert result.returncode == code
    assert (
        expected.encode("utf-8") in result.stdout + result.stderr
        or expected == "Składnia poprawna"
        and b"Sk" in result.stdout
    )


def test_all_examples_parse():
    for path in (Path(__file__).parents[1] / "examples").glob("*.kit"):
        assert Parser(path.read_text(encoding="utf-8")).parse()


def test_property_expression_and_state_conditions():
    out = []
    r = Interpreter(output=out.append).execute("""[create gui.menu="m"]
[create item.button="b"]
b.visible/true and not false
b.disabled/false or false
m.size/(1000,700)
if b.visible and not b.disabled:
    print("ready")
""")
    assert out == ["ready"]
    assert r.read("m", "size") == (1000, 700)


def test_function_lexical_scope():
    out = []
    Interpreter(output=out.append).execute("""var x = 3
function f(name):
    var x = 9
    print(name + str(x))
f("local=")
print(x)
""")
    assert out == ["local=9", 3]


def test_recursion_limit():
    with pytest.raises(KitleanError, match="rekurencji"):
        Interpreter().execute("function f():\n    f()\nf()")


def test_comments_and_unicode():
    out = []
    Interpreter(output=lambda *x: out.append(x)).execute(
        '# komentarz\nvar liczba = 2 # test\nprint("Zażółć # gęślą", liczba)'
    )
    assert out == [("Zażółć # gęślą", 2)]
