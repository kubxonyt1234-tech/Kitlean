from pathlib import Path

import pytest

from kitlean.errors import KitleanError
from kitlean.interpreter import Interpreter

pytestmark = pytest.mark.gui
EXAMPLES = Path(__file__).parents[1] / "examples"


@pytest.fixture
def game(tmp_path):
    i = Interpreter()
    r = i.runtime
    r.configure_program(EXAMPLES / "test04.kit", tmp_path / "data")
    try:
        r.windows.ensure()
    except KitleanError as error:
        pytest.skip(str(error))
    i.execute("""[create gui.menu/$Game 0.4$="game"]
game.size=(320,240)
[create item.sprite/assets/player.png="player"]
player.position=(100,100)
""")
    yield i
    r.windows.close()


def test_canvas_camera_rounding_and_actions(game):
    i = game
    r = i.runtime
    i.execute("""[create item.button/$Click$="button1"]
button1.background=#FF6600
button1.rounded=12
button1.align=center
button1.margin=10
var/hits = 0
when button1.clicked:
    hits += 1
game.camera.follow=player
game.camera.zoom=1.5
""")
    r.windows.open("game")
    r.windows.root.update()
    button = r.get("button1").widget
    assert button["rounded"] == 12 and button["background"] == "#FF6600"
    assert button.winfo_x() == 80
    button.invoke()
    assert i.env.get("hits") == 1
    photo = r.get("player").world_photo
    assert photo.width() == 36 and photo.height() == 48
    item = r.windows.canvas_items["game"]["player"]
    canvas = r.windows.canvases["game"]
    assert canvas.coords(item) == pytest.approx([160, 120])
    i.execute("player.action.rotate(90)")
    assert r.get("player").world_photo.width() == 48
    i.execute("player.action.hide")
    assert "player" not in r.windows.canvas_items["game"]
    i.execute("player.action.show\ngame.fullscreen=true")
    assert bool(r.windows.root.attributes("-fullscreen"))
    i.execute("game.fullscreen=false")


def test_mouse_and_new_keyboard_events(game):
    i = game
    r = i.runtime
    i.execute("""var/clicks = 0
var/keys = 0
when mouse.left.clicked:
    clicks += 1
when mouse.right.clicked:
    clicks += 10
when key.SPACE.pressed:
    keys += 1
""")
    r.windows.open("game")
    root = r.windows.root
    root.focus_force()
    root.update()
    canvas = r.windows.canvases["game"]
    canvas.event_generate("<Button-1>", x=22, y=33)
    canvas.event_generate("<Button-3>", x=42, y=53)
    root.event_generate("<KeyPress-space>")
    root.event_generate("<KeyRelease-space>")
    root.update()
    assert i.env.get("clicks") == 11 and i.env.get("keys") == 1
    assert r.world.mouse == pytest.approx((42, 53))


def test_forever_thene_and_segment_rendering(game):
    i = game
    r = i.runtime
    transitions = []
    source = """[create item.sprite/assets/zombie.png="zombie"]
zombie.save=npc
repeat forever:
    if player.outof.gui.game:
        create game.gui.next
        thene summon random.npc/zombie
        thene del game.last=copy
"""

    def cross(index=0):
        if index == 8:
            assert len(r.world.sprites("game")) == 1
            assert len(r.windows.canvases) == 1
            assert len(r.windows.canvas_items["game"]) == 1
            r.windows.close()
            return
        r.set("player", "position", (-1, 100) if index % 2 else (300, 100))

        def inspect():
            transitions.append(r.world.maps["game"].identifier)
            cross(index + 1)

        root.after(70, inspect)

    root = r.windows.root
    root.after(80, cross)
    root.after(4000, r.windows.close)
    i.execute(source + "\nrun game")
    assert transitions == ["game1", "game"] * 4
    assert not r.scheduler.jobs and not r.scheduler.coroutines


def test_async_thene_and_animation_event(game):
    i = game
    r = i.runtime
    i.execute("""var/done = false
var/finished = 0
when player.animation.finished:
    finished += 1
player.animation.speed=10
player.action.animate(bounce)
""")
    async_observation = []

    def begin():
        i.execute("wait/0.03\nthene player.action.hide\nthene done = true")
        assert i.env.get("done") is False

    def inspect():
        async_observation.append(
            (
                i.env.get("done"),
                r.get("player").properties["visible"],
                i.env.get("finished"),
            )
        )
        r.windows.close()

    r.windows.root.after(30, begin)
    r.windows.root.after(230, inspect)
    i.execute("run game")
    # Hidden sprites intentionally pause simulation; completion is tested separately.
    assert async_observation[0][:2] == (True, False)


@pytest.mark.parametrize(
    "filename",
    [
        "clicker.kit",
        "movement.kit",
        "animations.kit",
        "collisions.kit",
        "gravity.kit",
        "camera.kit",
        "infinite_world.kit",
        "npc_spawn.kit",
        "gui_styles.kit",
    ],
)
def test_examples04_smoke(tmp_path, filename):
    i = Interpreter()
    r = i.runtime
    r.configure_program(EXAMPLES / filename, tmp_path / "smoke")
    try:
        r.windows.ensure()
    except KitleanError as error:
        pytest.skip(str(error))
    source = (EXAMPLES / filename).read_text(encoding="utf-8")
    r.windows.root.after(180, r.windows.close)
    try:
        i.execute(source)
    finally:
        r.windows.close()
    assert not r.scheduler.jobs and r.windows.root is None


def test_live_animation_completion(game):
    i = game
    r = i.runtime
    i.execute(
        "var/finished = 0\nwhen player.animation.finished:\n    finished += 1\nplayer.animation.speed=10\nplayer.action.animate(rotate)"
    )
    r.windows.root.after(300, r.windows.close)
    i.execute("run game")
    assert i.env.get("finished") == 1
