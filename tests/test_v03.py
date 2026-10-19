import pytest

from kitlean.errors import KitleanError, KitleanMathError
from kitlean.interpreter import Interpreter
from kitlean.parser import Parser
from kitlean.runtime import Runtime
from kitlean.storage import Storage


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("10 : 4", 2.5),
        ("(10 + 5) : 3", 5),
        ("2 + 3 * 4 : 2", 8),
        ("2 ** 3 ** 2", 512),
        ("-2 ** 2", -4),
        ("2 ** -2", 0.25),
        ("17 % 5", 2),
        ("math/round(3.76)", 4),
        ("math/sqrt(25)", 5),
        ("math/abs(-10)", 10),
        ("math/min(5,10)", 5),
        ("math/max(5,10)", 10),
        ("math/pow(2,3)", 8),
        ("math/nww(4,6)", 12),
        ("math/nwd(12,18)", 6),
        ("math/nww(-12,18)", 36),
        ("math/nwd(-12,-18)", 6),
        ("math/nwd(0,0)", 0),
        ("math/nww(0,9)", 0),
        ("[1,2][1] + 3", 5),
        ("1 < 2 < 3", True),
        ("2 in [1,2]", True),
        ("4 not in [1,2]", True),
        ("not false and true", True),
    ],
)
def test_math(expression, expected):
    i = Interpreter()
    i.execute("var/result = " + expression)
    assert i.env.get("result") == expected


def test_colon_block_and_augmented():
    i = Interpreter()
    i.execute("""var/x = 10
x += 5
x -= 2
x *= 3
x := 2
if x : 2 > 5:
    var/result = x
""")
    assert i.env.get("result") == 19.5
    assert Parser("x := 2").parse()[0].kind == "augment"


@pytest.mark.parametrize(
    "expression",
    [
        "1 : 0",
        "math/sqrt(-1)",
        "math/nww(2.5,3)",
        "math/nwd(true,2)",
        "math/random(5,1)",
        "math/random(1.1,4)",
        "math/abs($text$)",
        "math/unknown(1)",
        "math/pow(0,-1)",
    ],
)
def test_math_errors(expression):
    with pytest.raises(KitleanMathError) as info:
        Interpreter().execute("var/x = 0\nvar/x = " + expression)
    assert info.value.line == 2


def test_random():
    i = Interpreter()
    i.execute("repeat 100:\n    var/x = math/random(1,2)")
    assert i.env.get("x") in (1, 2)


def test_default_references_scoped():
    i = Interpreter()
    r = i.execute("""create gui/menu
create item/button/First
button.text/Updated
[create item/button="explicit"]
button.text/Latest
[create gui/menu="other"]
""")
    assert r.objects["_anon_2"].properties["text"] == "Updated"
    assert r.get("explicit").properties["text"] == "Latest"
    with pytest.raises(KitleanError):
        r.get("button")
    i.execute("create item/button/New")
    assert r.get("button").parent == "other"
    # Jawny alias ma pierwszeństwo przed skrótem typu, zgodność ze starymi programami.
    i.execute('[create item/label="label"]\nlabel.text/OK')
    assert r.get("label").properties["text"] == "OK"


def test_storage_roundtrip_projects_and_corruption(tmp_path):
    i = Interpreter()
    i.runtime.configure_program(tmp_path / "one/game.kit", tmp_path / "data")
    i.execute("var/points = [1, $Jan$, true, [2.5, null]]\nsave points")
    j = Interpreter()
    j.runtime.configure_program(tmp_path / "one/game.kit", tmp_path / "data")
    j.execute("var/points = 0\nload points")
    assert j.env.get("points") == [1, "Jan", True, [2.5, None]]
    other = Storage(tmp_path / "two/game.kit", tmp_path / "data")
    assert other.load("points", 10, 1) == 10
    path = j.runtime.storage.path
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(KitleanError):
        j.execute("load points")
    assert not list(path.parent.glob("tmp*"))


def test_load_notifies_binding(tmp_path):
    i = Interpreter()
    r = i.runtime
    r.configure_program(tmp_path / "game.kit", tmp_path / "data")
    i.execute("""create gui/menu
var/points = 7
save points
create item/label/$Punkty: {points}$
points = 0
load points
""")
    assert r.get("label").properties["text"] == "Punkty: 7"


@pytest.mark.parametrize(
    "source",
    [
        "create timer\ntimer.interval/0",
        "create timer\ntimer.loop/1",
        "create audio/music\naudio.volume/101",
        "create audio/music\naudio.file/missing.wav",
        "wait/-1",
        "if key/F99.pressed:\n    print(1)",
    ],
)
def test_resource_errors(source):
    with pytest.raises(KitleanError):
        Interpreter().execute(source)


def test_windows_path_literal():
    node = Parser(r"audio.file/$C:\My Music\background.mp3$").parse()[0]
    template = node.args[2].tree
    assert Runtime().render_template(template, None, 1) == r"C:\My Music\background.mp3"


def test_all_keyboard_names_parse():
    from kitlean.keyboard import KEYS

    for key in KEYS:
        node = Parser(f"if key/{key}.pressed:\n    print(1)").parse()[0]
        assert node.kind == "key_event"
        assert Interpreter().runtime.keyboard.canonical(node.args[0], 1) == KEYS[key]
