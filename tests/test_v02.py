import ast

import pytest

from kitlean.ast_nodes import Template
from kitlean.errors import KitleanError
from kitlean.interpreter import Interpreter
from kitlean.parser import Parser

BASE = '[create gui/menu="game"]\n[create item/label="counter"]\n'


def test_anonymous_creation():
    r = Interpreter().execute(
        "create gui/menu\ncreate item/button/KLIKNIJ!\ncreate item/button/$Drugi przycisk$"
    )
    objects = list(r.objects.values())
    assert [x.kind for x in objects] == ["gui.menu", "item.button", "item.button"]
    assert len({x.name for x in objects}) == 3
    assert objects[1].parent == objects[0].name
    assert objects[1].properties["text"] == "KLIKNIJ!"
    assert objects[2].properties["text"] == "Drugi przycisk"


def test_alias_commands_parse():
    nodes = Parser(
        '[create gui/menu="game"]\nrun game\nopen game\nclose game\nrun'
    ).parse()
    assert [n.kind for n in nodes] == ["create", "run", "open", "close", "run_context"]
    assert nodes[1].args[0].tree.value == "game"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("KLIKNIJ!", "KLIKNIJ!"),
        ("$KLIKNIJ MNIE!$", "KLIKNIJ MNIE!"),
        (
            '$Zażółć gęślą jaźń! # / [] () "test" 😀$',
            'Zażółć gęślą jaźń! # / [] () "test" 😀',
        ),
        (
            r"$Cena: 5\$; \{dosłownie\}; C:\\gry\nNowa\tlinia$",
            "Cena: 5$; {dosłownie}; C:\\gry\nNowa\tlinia",
        ),
        ("$$", ""),
    ],
)
def test_text(value, expected):
    r = Interpreter().execute(BASE + "counter.text/" + value)
    assert r.read("counter", "text") == expected


def test_dependency_updates_and_replacement():
    i = Interpreter()
    r = i.execute(
        BASE
        + """var/coins = 5
var/level = 1
counter.text/$Monety: {coins} | Poziom: {level}$
[create item/label="other"]
other.text/$Monety: {coins}$
"""
    )
    template = r.bindings[("counter", "text")][0]
    assert isinstance(template, Template)
    i.execute("coins = coins + 1\nlevel = 2")
    assert r.read("counter", "text") == "Monety: 6 | Poziom: 2"
    assert r.read("other", "text") == "Monety: 6"
    assert r.bindings[("counter", "text")][0] is template
    i.execute("counter.text/Stały\ncoins = 9")
    assert r.read("counter", "text") == "Stały"
    assert r.read("other", "text") == "Monety: 9"
    assert ("counter", "text") not in r.bindings


def test_variables_expressions_and_template_output():
    out = []
    i = Interpreter(output=lambda *args: out.append(args))
    i.execute("""var/points = 10 / 2
var/name = $Jan Kowalski$
var/active = true
points = points + 1
print($Gracz: {name}; punkty: {points}; aktywny: {active}$)
var values = [1, false, null]
print(values[1])
""")
    assert out == [("Gracz: Jan Kowalski; punkty: 6.0; aktywny: true",), (False,)]


def test_clicker_events_no_duplicate_and_scope():
    i = Interpreter()
    r = i.execute(
        BASE
        + """var/points = 0
counter.text/$Punkty: {points}$
[create item/button="click"]
repeat 5:
    if click.clicked:
        points = points + 1
function add():
    points = points + 1
"""
    )
    assert len(r.events.handlers[("click", "clicked")]) == 1
    for number in range(1, 51):
        r.events.emit(r.get("click"), "clicked")
        assert i.env.get("points") == number
        assert r.read("counter", "text") == f"Punkty: {number}"
    i.execute("add()")
    assert r.read("counter", "text") == "Punkty: 51"
    r.set("click", "disabled", True)
    r.events.emit(r.get("click"), "clicked")
    assert i.env.get("points") == 51


def test_legacy_literal_dollars_and_comment():
    out = []
    Interpreter(output=out.append).execute('print("literal $ {x}") # $ not opened')
    assert out == ["literal $ {x}"]


@pytest.mark.parametrize(
    "source,line,fragment",
    [
        ("var/x = 1\nprint($niezamknięte)", 2, "zamykającego"),
        (BASE + "counter.text/Hello World", 3, "Invalid text value"),
        (BASE + "counter.text/$Punkty: {missing}$", 3, "interpolacji"),
        ('[create gui/menu="game"]\n[create gui/menu="game"]', 2, "istnieje"),
        ("unknown.text/Hello", 1, "Unknown object"),
        ('[create gui/menu="g"]\ng.size/(0,10)', 2, "Wymagana para"),
        ('[create gui/menu="g"]\ng.visible/Hello', 2, "identyfikator"),
        ('[create gui//menu="g"]', 1, "create"),
        (BASE + "counter.text/", 3, "Brak wartości"),
        ("print($bad {a + 1}$)", 1, "Interpolacja"),
        (r"print($bad \q$)", 1, "ucieczki"),
    ],
)
def test_new_errors(source, line, fragment):
    with pytest.raises(KitleanError) as info:
        Interpreter().execute(source)
    assert info.value.line == line
    assert fragment in str(info.value)


def test_anonymous_run_requires_menu():
    with pytest.raises(KitleanError):
        Interpreter().execute("run")


def test_dollar_is_ast_node():
    expression = Parser("print($Hello$)").parse()[0].args[0].tree
    assert isinstance(expression, ast.Call)
    assert isinstance(expression.args[0], Template)


def test_cli_exact_version():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "kitlean", "--version"], capture_output=True, check=False
    )
    assert result.returncode == 0
    assert result.stdout.decode().splitlines() == [
        "Kitlean 0.2 Beta",
        "Python-powered programming language",
    ]


def test_binding_scope_and_rebinding():
    i = Interpreter()
    r = i.execute(
        BASE
        + """var/points = 1
function setup():
    counter.text/$Globalne: {points}$
    var/points = 500
setup()
points = 2
"""
    )
    assert r.read("counter", "text") == "Globalne: 2"
    i.execute("counter.text/$Nowe: {points}$\npoints = 3")
    assert r.read("counter", "text") == "Nowe: 3"
    assert len(r.dependencies[(i.env, "points")]) == 1


@pytest.mark.parametrize(
    "source, line",
    [
        ("var/x = 1\nopen missing", 2),
        ("var/x = 1\nclose missing", 2),
        ("var/x = 1\nrun missing", 2),
        (BASE + "counter.disabled/$false$", 3),
        (BASE + "counter.text/$bad }$", 3),
    ],
)
def test_more_error_lines(source, line):
    with pytest.raises(KitleanError) as info:
        Interpreter().execute(source)
    assert info.value.line == line
