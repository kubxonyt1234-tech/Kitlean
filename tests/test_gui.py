from pathlib import Path

import pytest

from kitlean.errors import KitleanError
from kitlean.interpreter import Interpreter

pytestmark = pytest.mark.gui


@pytest.fixture
def interpreter():
    i = Interpreter()
    try:
        i.runtime.windows.ensure()
    except KitleanError as e:
        pytest.skip(str(e))
    yield i
    i.runtime.windows.close()


def test_real_widgets_layout_and_properties(interpreter):
    i = interpreter
    r = i.execute("""[create gui.menu="m"]
[create item.button="b"]
b.text/"Button"
[create item.input="entry"]
entry.value/"Test"
[create item.label="label"]
label.text/"Natural label"
[create item.checkbox="check"]
check.text/"Choice"
""")
    r.windows.open("m")
    r.windows.root.update()
    assert r.get("m").widget.winfo_width() == 800
    assert r.get("b").widget.winfo_width() == 160
    assert r.get("b").widget.winfo_height() == 45
    assert r.get("entry").widget.winfo_width() == 240
    assert r.get("entry").widget.winfo_height() == 40
    children = [r.get(n).widget for n in ("b", "entry", "label", "check")]
    assert all(
        b.winfo_y() >= a.winfo_y() + a.winfo_height() + 12
        for a, b in zip(children, children[1:], strict=False)
    )
    assert r.read("entry", "value") == "Test"
    r.set("entry", "text", "Changed")
    assert r.get("entry").widget.get() == "Changed"
    r.get("entry").widget.delete(0, "end")
    r.get("entry").widget.insert(0, "User input")
    i.execute('[create gui.menu="other"]')
    r.set("entry", "parent", "other")
    assert r.read("entry", "value") == "User input"
    r.get("check").widget.invoke()
    assert r.read("check", "value") is True
    r.set("b", "size", (250, 60))
    r.set("b", "position", (70, 80))
    r.windows.root.update()
    assert (r.get("b").widget.winfo_x(), r.get("b").widget.winfo_y()) == (70, 80)
    assert r.get("b").widget.winfo_width() == 250
    r.set("b", "visible", False)
    r.windows.root.update()
    assert not r.get("b").widget.winfo_ismapped()
    r.set("b", "visible", True)
    r.set("b", "disabled", True)
    assert str(r.get("b").widget["state"]) == "disabled"


def test_real_events_and_switching(interpreter):
    out = []
    interpreter.output = out.append
    interpreter.builtins["print"] = out.append
    r = interpreter.execute("""[create gui.menu="m"]
[create item.button="b"]
[create gui.menu="settings"]
if b.clicked:
    open.gui.menu("settings")
if b.hovered:
    print("hover")
""")
    r.windows.open("m")
    r.windows.root.update()
    r.get("b").widget.event_generate("<Enter>")
    r.windows.root.update()
    assert out == ["hover"]
    r.get("b").widget.invoke()
    r.windows.root.update()
    assert r.windows.active == "settings"
    r.windows.hide("settings")
    assert r.windows.active is None
    r.windows.open("m")
    r.windows.root.update()
    assert r.get("m").widget.winfo_ismapped()


def test_demo_mainloop(interpreter):
    i = interpreter
    out = []
    i.builtins["print"] = out.append
    source = (Path(__file__).parents[1] / "examples/main_menu.kit").read_text(
        encoding="utf-8"
    )
    observations = []

    def interact():
        r = i.runtime
        observations.append(r.windows.active)
        r.get("start").widget.invoke()
        r.get("settings").widget.invoke()
        observations.append(r.windows.active)
        r.get("back").widget.invoke()
        observations.append(r.windows.active)
        r.get("exit").widget.invoke()

    i.runtime.windows.root.after(150, interact)
    i.execute(source)
    assert observations == ["MainMenu", "Settings", "MainMenu"]
    assert out == ["Uruchomiono!"]
    assert i.runtime.windows.root is None


def test_callback_error_is_language_error(interpreter):
    i = interpreter
    i.execute(
        '[create gui.menu="m"]\n[create item.button="b"]\nif b.clicked:\n    print(1/0)'
    )
    i.runtime.windows.root.after(100, lambda: i.runtime.get("b").widget.invoke())
    with pytest.raises(KitleanError):
        i.runtime.windows.run("m")


def test_v02_clicker_real_mainloop(interpreter):
    i = interpreter
    source = (Path(__file__).parents[1] / "examples/clicker.kit").read_text(
        encoding="utf-8-sig"
    )
    observations = []

    def interact():
        r = i.runtime
        root = r.windows.root
        button = r.get("click").widget
        counter = r.get("counter").widget
        assert counter["text"] == "Punkty: 0"
        assert root.winfo_width() == 800
        assert root.winfo_height() == 500
        assert (button.winfo_width(), button.winfo_height()) == (160, 45)
        assert button.winfo_y() >= counter.winfo_y() + counter.winfo_height() + 12
        original_build = r.windows.build

        def unexpected_build():
            raise AssertionError("Odświeżanie licznika nie może przebudowywać GUI")

        r.windows.build = unexpected_build
        for points in range(1, 101):
            button.invoke()
            assert i.env.get("points") == points
            assert counter["text"] == f"Punkty: {points}"
            assert r.windows.root is root
            assert r.get("click").widget is button
            assert r.get("counter").widget is counter
        r.windows.build = original_build
        i.execute(
            '[create gui/menu="settings"]\nopen settings\nopen game\nopen settings\nopen game'
        )
        button.invoke()
        observations.append((i.env.get("points"), counter["text"]))
        assert len(r.events.handlers[("click", "clicked")]) == 1
        r.windows.close()

    i.runtime.windows.root.after(150, interact)
    i.runtime.windows.root.after(10000, i.runtime.windows.close)
    i.execute(source)
    assert observations == [(101, "Punkty: 101")]


def test_v02_clicker_cli_run(interpreter, monkeypatch):
    from kitlean import cli

    i = interpreter
    observed = []

    def interact():
        r = i.runtime
        for _ in range(10):
            r.get("click").widget.invoke()
        observed.append(r.get("counter").widget["text"])
        r.windows.close()

    i.runtime.windows.root.after(150, interact)
    i.runtime.windows.root.after(10000, i.runtime.windows.close)
    # Dostarczamy tylko timer do prawdziwego interpretera; okna i widgety są rzeczywiste.
    monkeypatch.setattr(cli, "Interpreter", lambda: i)
    path = Path(__file__).parents[1] / "examples/clicker.kit"
    assert cli.main(["run", str(path)]) == 0
    assert observed == ["Punkty: 10"]
