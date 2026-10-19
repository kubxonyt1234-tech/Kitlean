from pathlib import Path

import pytest

from kitlean.errors import KitleanError
from kitlean.interpreter import Interpreter

pytestmark = pytest.mark.gui
ASSETS = Path(__file__).parents[1] / "examples/assets"


@pytest.fixture
def interpreter():
    i = Interpreter()
    try:
        i.runtime.windows.ensure()
    except KitleanError as e:
        pytest.skip(str(e))
    yield i
    i.runtime.windows.close()


@pytest.mark.parametrize("extension", ["png", "jpg", "webp"])
def test_images_actual(interpreter, extension):
    i = interpreter
    r = i.runtime
    r.configure_program(ASSETS.parent / "images.kit")
    i.execute(f"create gui/menu\ncreate item/image\nimage.file/assets/logo.{extension}")
    r.windows.open("gui")
    r.windows.root.update()
    i.execute("var/clicks = 0\nif image.clicked:\n    clicks += 1")
    e = r.get("image")
    e.widget.event_generate("<Button-1>")
    r.windows.root.update()
    assert i.env.get("clicks") == 1
    assert e.image.width() <= 320 and e.image.height() <= 240
    assert e.image.width() == 2 * e.image.height()
    i.execute("image.size/(100,100)\nimage.position/(50,50)")
    r.windows.root.update()
    assert (e.image.width(), e.image.height()) == (100, 50)
    assert (e.widget.winfo_x(), e.widget.winfo_y()) == (50, 50)
    i.execute("image.visible/false")
    r.windows.root.update()
    assert not e.widget.winfo_ismapped()


def test_wait_nested_functions_and_timers(interpreter):
    i = interpreter
    r = i.runtime
    i.execute("""create gui/menu
var/ticks = 0
var/done = false
create item/label/$Ticks: {ticks}$
[create timer="clock"]
clock.interval/0.01
clock.loop/true
if clock.tick:
    ticks += 1
function delayed():
    repeat 2:
        wait/0.03
    done = true
    stop clock
    close.app
create item/button/START
if button.clicked:
    delayed()
""")

    def click():
        r.get("button").widget.invoke()

    r.windows.root.after(30, click)
    r.windows.root.after(3000, r.windows.close)
    i.execute("start clock\nrun gui")
    assert i.env.get("done") is True
    assert i.env.get("ticks") >= 3
    assert not r.scheduler.jobs and not r.scheduler.coroutines and not r.timers


def test_key_repeat_and_entry_focus(interpreter):
    i = interpreter
    r = i.runtime
    i.execute("""create gui/menu
var/points = 0
if key/SPACE.pressed:
    points += 1
create item/input
""")
    r.windows.open("gui")
    root = r.windows.root
    root.focus_force()
    root.update()
    root.event_generate("<KeyPress-space>")
    root.event_generate("<KeyPress-space>")
    root.update()
    assert i.env.get("points") == 1
    root.event_generate("<KeyRelease-space>")
    root.event_generate("<KeyPress-space>")
    root.update()
    assert i.env.get("points") == 1  # para release/press autorepeat przed idle
    root.event_generate("<KeyRelease-space>")
    root.update()
    root.event_generate("<KeyPress-space>")
    root.update()
    assert i.env.get("points") == 2
    root.event_generate("<KeyRelease-space>")
    root.update()
    entry = r.get("input").widget
    entry.focus_force()
    root.update()
    entry.event_generate("<KeyPress-space>")
    entry.event_generate("<KeyRelease-space>")
    root.update()
    assert i.env.get("points") == 2


def test_clicker03_save_audio_and_second_launch(interpreter, tmp_path):
    i = interpreter
    r = i.runtime
    r.configure_program(ASSETS.parent / "clicker_03.kit", tmp_path / "data")
    source = (ASSETS.parent / "clicker_03.kit").read_text(encoding="utf-8")
    observed = []

    def play():
        button = r.get("click").widget
        for _ in range(3):
            button.invoke()
        channel = r.audio.items["song"][2]
        assert channel.get_busy()
        observed.append(r.get("label").widget["text"])
        assert len(r.audio.items) == 1
        r.windows.close()

    r.windows.root.after(100, play)
    r.windows.root.after(3000, r.windows.close)
    i.execute(source)
    assert observed == ["Punkty: 3"]
    assert r.audio.mixer is None
    # Nowy interpreter w tym samym projekcie ładuje zapis, bez odtwarzania.
    second = Interpreter()
    second.runtime.configure_program(
        ASSETS.parent / "clicker_03.kit", tmp_path / "data"
    )
    second.execute("var/points = 0\nload points")
    assert second.env.get("points") == 3


def test_wait_startup(interpreter):
    out = []
    i = interpreter
    i.builtins["print"] = out.append
    i.execute("print($before$)\nwait/0.02\nprint($after$)")
    assert out == ["before", "after"]


def test_close_cancels_waiting_handler(interpreter):
    i = interpreter
    r = i.runtime
    i.execute("""create gui/menu
var/done = false
create item/button/Wait
if button.clicked:
    wait/10
    done = true
""")
    root = r.windows.root
    root.after(30, lambda: r.get("button").widget.invoke())
    root.after(60, r.windows.close)
    i.execute("run gui")
    assert i.env.get("done") is False
    assert not r.scheduler.jobs and not r.scheduler.coroutines


def test_close_stops_following_statements(interpreter):
    i = interpreter
    i.execute("var/done = false\nclose.app\nwait/10\ndone = true")
    assert i.env.get("done") is False
    assert not i.runtime.scheduler.jobs
    assert i.runtime.windows.root is None


def test_corrupt_image_error(interpreter, tmp_path):
    (tmp_path / "bad.png").write_text("broken", encoding="utf-8")
    i = interpreter
    i.runtime.configure_program(tmp_path / "program.kit")
    with pytest.raises(KitleanError) as info:
        i.execute("create gui/menu\ncreate item/image\nimage.file/bad.png")
    assert info.value.line == 3
