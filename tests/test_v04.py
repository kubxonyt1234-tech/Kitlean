import math
from pathlib import Path

import pytest

from kitlean.errors import KitleanError
from kitlean.interpreter import Interpreter
from kitlean.parser import Parser

EXAMPLES = Path(__file__).parents[1] / "examples"


@pytest.fixture
def game(tmp_path):
    i = Interpreter()
    i.runtime.configure_program(EXAMPLES / "test04.kit", tmp_path / "saves")
    i.execute("""[create gui.menu/Gra="game"]
game.size=(320,240)
[create item.sprite/assets/player.png="player"]
player.position=(100,100)
""")
    yield i
    i.runtime.windows.close()


def test_new_creation_and_symbols(game):
    i = game
    r = i.runtime
    i.execute("""var/points = 2
[create item.button/$Kliknij mnie$="click"]
[create item.label/$Punkty: {points}$="counter"]
click.background=#FF6600
click.rounded=12
click.margin=10
click.align=center
click.visible=true
points += 1
create item.button/START
""")
    assert r.get("game").properties["title"] == "Gra"
    assert r.get("click").properties["background"] == "#FF6600"
    assert r.get("counter").properties["text"] == "Punkty: 3"
    assert r.get("button").properties["text"] == "START"
    assert r.get("button") is not r.get("click")


def test_actions_and_independent_copy(game):
    i = game
    r = i.runtime
    i.execute(
        "player.action.move(10,-5)\nplayer.action.teleport(20,30)\nplayer.action.rotate(90)\nplayer.action.hide\ncreate player.copy"
    )
    original = r.get("player")
    clone = r.get("sprite")
    assert clone.name != original.name and clone.properties is not original.properties
    i.execute("player.action.show\nplayer.action.move(5,0)")
    assert original.properties["position"] == (25, 30)
    assert clone.properties["position"] == (20, 30)
    assert (
        clone.properties["visible"] is False and original.properties["visible"] is True
    )
    i.execute("del " + clone.name)
    assert clone.name not in r.objects


def test_movement_fps_independence_and_diagonal(game):
    i = game
    r = i.runtime
    i.execute("player.setting.move=wsad/10")
    r.keyboard.down.update(("w", "d"))
    for _ in range(60):
        r.world.advance(1 / 60)
    x, y = r.get("player").properties["position"]
    assert math.hypot(x - 100, y - 100) == pytest.approx(10, abs=1e-8)
    i.execute("player.position=(100,100)\nplayer.setting.move=arrows/10")
    r.keyboard.down = {"Up", "Right"}
    for _ in range(30):
        r.world.advance(1 / 30)
    assert r.get("player").properties["position"] == pytest.approx((x, y), abs=1e-8)


def test_collision_enter_and_disable(game):
    i = game
    r = i.runtime
    i.execute("""var/hits = 0
[create item.sprite/assets/zombie.png="enemy"]
enemy.position=(110,100)
enemy.collision=true
player.collision=true
when player.collided.enemy:
    hits += 1
""")
    for _ in range(20):
        r.world.advance(1 / 60)
    assert i.env.get("hits") == 1
    i.execute("enemy.collision=false")
    r.world.advance(0.02)
    i.execute("enemy.collision=true")
    r.world.advance(0.02)
    assert i.env.get("hits") == 2
    i.execute("enemy.action.hide")
    r.world.advance(0.02)
    assert not r.world.contacts


def test_gravity_jump_and_no_double_jump(game):
    i = game
    r = i.runtime
    i.execute("player.gravity=98\nplayer.collision=true\nplayer.position=(100,208)")
    r.world.advance(0.1)
    player = r.get("player")
    assert player.grounded
    i.execute("player.action.jump(30)")
    velocity = player.velocity
    i.execute("player.action.jump(30)")
    assert player.velocity == velocity
    r.world.advance(0.2)
    assert player.properties["position"][1] < 208
    r.world.advance(2)
    assert player.grounded and player.properties["position"][1] == pytest.approx(208)
    i.execute("player.gravity=0\nplayer.position=(100,100)")
    r.world.advance(1)
    assert player.properties["position"] == (100, 100)


@pytest.mark.parametrize("animation", ["bounce", "rotate", "fade"])
def test_animation_end_event(game, animation):
    i = game
    r = i.runtime
    i.execute(f"""var/finished = 0
player.animation.speed=2
when player.animation.finished:
    finished += 1
player.action.animate({animation})
""")
    r.world.advance(0.6)
    assert i.env.get("finished") == 1
    assert r.get("player").animation_state is None
    r.world.advance(0.6)
    assert i.env.get("finished") == 1
    i.execute("player.animation.loop=true\nplayer.action.animate(" + animation + ")")
    r.world.advance(1.1)
    assert i.env.get("finished") == 3


def test_camera_does_not_move_world(game):
    i = game
    r = i.runtime
    i.execute("game.camera.follow=player\ngame.camera.zoom=1.5")
    before = r.get("player").properties["position"]
    x, y = r.world.screen_position("player")
    w, h = r.world.dimensions(r.get("player"))
    assert x + w * 1.5 / 2 == pytest.approx(160)
    assert y + h * 1.5 / 2 == pytest.approx(120)
    assert r.get("player").properties["position"] == before
    r.world.mouse = (25, 40)
    i.execute("var/mousePoint = mouse.position")
    assert i.env.get("mousePoint") == (25, 40)


def prepare_npc(i):
    i.execute("""[create item.sprite/assets/zombie.png="zombie"]
zombie.speed=3
zombie.collision=true
zombie.save=npc
""")


def test_npc_template_alias_and_positions(game):
    i = game
    r = i.runtime
    prepare_npc(i)
    i.execute("""summon npc/zombie=(10,10)
[summon random.npc/zombie="enemy1"]
enemy1.speed=5
summon npc/zombie=player
summon random.npc/zombie=game
""")
    instances = [e for e in r.world.sprites("game") if e.name != "player"]
    assert len(instances) == 4
    assert r.world.templates["zombie"]["speed"] == 3
    assert r.get("zombie").template
    assert r.get("enemy1").properties["speed"] == 5
    assert all(e.properties is not r.world.templates["zombie"] for e in instances)
    for e in instances:
        x, y, right, bottom = r.world.bounds(e)
        assert 0 <= x < right <= 320 and 0 <= y < bottom <= 240


def transition(i, direction):
    r = i.runtime
    p = r.get("player")
    width, height = r.get("game").properties["size"]
    w, h = r.world.dimensions(p)
    position = {
        "right": (width - w + 1, 100),
        "left": (-1, 100),
        "down": (100, height - h + 1),
        "up": (100, -1),
    }[direction]
    r.set("player", "position", position)
    i.execute("""if player.outof.gui.game:
    create game.gui.next
    thene summon random.npc/zombie
    thene del game.last=copy
""")


def test_segments_roundtrip_memory_and_state(game):
    i = game
    r = i.runtime
    prepare_npc(i)
    i.execute('[summon npc/zombie="first"]\nfirst.position=(10,10)\nfirst.speed=77')
    actor = r.get("player")
    actor.properties["speed"] = 123
    transition(i, "right")
    manager = r.world.maps["game"]
    assert manager.identifier == "game1" and manager.previous == "game"
    assert "first" not in r.objects
    assert len(r.world.sprites("game")) == 2
    transition(i, "left")
    assert manager.identifier == "game" and manager.restored
    assert r.get("first").properties["speed"] == 77
    assert len(r.world.sprites("game")) == 2  # traveler + restored NPC, no extra spawn
    assert r.get("player") is actor and actor.properties["speed"] == 123
    for _ in range(50):
        transition(i, "right")
    assert len(r.objects) <= 4  # menu, traveler, template, one active NPC
    assert len(r.world.images) <= 32 and len(r.world.maps) == 1
    for _ in range(50):
        transition(i, "left")
    assert manager.coord == (0, 0) and r.get("first").properties["speed"] == 77
    assert r.get("player") is actor
    transition(i, "down")
    assert manager.coord == (0, 1)
    transition(i, "up")
    assert manager.coord == (0, 0)
    assert (
        manager.connection.execute("SELECT COUNT(*) FROM segments").fetchone()[0] == 52
    )


def test_edge_trigger_and_thene_rules(game):
    i = game
    r = i.runtime
    prepare_npc(i)
    r.set("player", "position", (-1, 100))
    assert r.world.outof("player", "game") is True
    assert r.world.outof("player", "game") is False
    i.execute("create game.gui.next\nthene del game.last=copy")
    manager = r.world.maps["game"]
    before = manager.identifier
    i.execute("create game.gui.next\nthene summon random.npc/zombie")
    assert manager.identifier == before and len(r.world.sprites("game")) == 1
    with pytest.raises(KitleanError):
        Parser("thene del game.last=copy").parse()
    with pytest.raises(KitleanError):
        i.execute("player.action.unknown\nthene del game.last=copy")
    assert r.get("player").name == "player"


@pytest.mark.parametrize(
    "source",
    [
        "player.action.move(1)",
        "player.action.animate(unknown)",
        "game.action.jump(1)",
        "player.action.jump(1)",
        "player.position=($bad$,0)",
        "player.gravity=-1",
        "player.setting.move=other/10",
        "game.camera.zoom=0",
        "when true:\n    print(1)",
        "summon npc/missing=(1,1)",
        "del missing",
        "create game.gui.next",
        '[summon random.npc/missing="x"]',
        "player.animation.speed=0",
    ],
)
def test_errors(game, source):
    with pytest.raises(KitleanError):
        game.execute(source)


def test_alias_after_punctuation(game):
    game.execute('[create item.button/KLIKNIJ!="click"]')
    assert game.runtime.get("click").properties["text"] == "KLIKNIJ!"


def test_segment_failure_preserves_objects(game):
    i = game
    r = i.runtime
    prepare_npc(i)
    i.execute('[create item.sprite/assets/zombie.png="game1"]')
    actor = r.get("player")
    old = r.get("game1")
    r.set("player", "position", (300, 100))
    assert r.world.outof("player", "game")
    with pytest.raises(KitleanError):
        i.execute("create game.gui.next\nthene del game.last=copy")
    assert r.get("player") is actor and r.get("game1") is old
    assert r.world.maps["game"].coord == (0, 0)


def test_random_spawn_failure_is_bounded(game):
    i = game
    r = i.runtime
    prepare_npc(i)
    i.execute(
        '[create item.sprite/assets/platform.png="wall"]\nwall.size=(3200,400)\nwall.position=(0,0)\nwall.collision=true'
    )
    before = set(r.objects)
    with pytest.raises(KitleanError):
        i.execute("summon random.npc/zombie")
    assert set(r.objects) == before


def test_plain_gui_boundary_is_edge_triggered(game):
    r = game.runtime
    r.set("player", "position", (-1, 100))
    assert r.world.outof("player", "game")
    assert not r.world.outof("player", "game")
    r.set("player", "position", (100, 100))
    assert not r.world.outof("player", "game")
    r.set("player", "position", (100, -1))
    assert r.world.outof("player", "game")


def test_no_alias_title_and_sprite(game):
    i = game
    r = i.runtime
    i.execute("create gui.menu/$Drugie menu$\ncreate item.sprite/assets/player.png")
    assert r.get("gui").properties["title"] == "Drugie menu"
    assert r.get("sprite").parent == r.get("gui").name


def test_thenes_after_success_and_failure(game):
    i = game
    i.execute("var/result = 0\nthene result += 1\nthene result += 2")
    assert i.env.get("result") == 3
    with pytest.raises(KitleanError):
        i.execute("var/x = 1 : 0\nthene result += 100")
    assert i.env.get("result") == 3
