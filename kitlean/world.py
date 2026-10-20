"""Deterministic 2D simulation, actions, NPCs and bounded resource caches."""

import copy
import math
import random
import time
from collections import OrderedDict

from PIL import Image

from .errors import KitleanError
from .segments import Segments


class World:
    def __init__(self, runtime):
        self.runtime = runtime
        self.templates = {}
        self.contacts = set()
        self.outside = set()
        self.pending = {}
        self.maps = {}
        self.images = OrderedDict()
        self.rng = random.Random()
        self.serial = 0
        self.job = None
        self.clock = 0.0
        self.accumulator = 0.0
        self.mouse = (0, 0)
        self.last_transition = None

    def unique(self, prefix):
        while True:
            self.serial += 1
            name = f"{prefix}_{self.serial}"
            if name not in self.runtime.objects:
                return name

    def sprites(self, menu=None):
        return [
            e
            for e in self.runtime.objects.values()
            if e.kind == "item.sprite"
            and not getattr(e, "template", False)
            and (menu is None or e.parent == menu)
        ]

    def source(self, value):
        path = str(self.runtime.asset_path(value))
        if path not in self.images:
            try:
                with Image.open(path) as image:
                    self.images[path] = image.convert("RGBA")
            except (OSError, ValueError) as error:
                raise KitleanError(
                    "Cannot load sprite: " + str(error), self.runtime.line
                ) from None
            if len(self.images) > 32:
                self.images.popitem(last=False)
        self.images.move_to_end(path)
        return self.images[path]

    def dimensions(self, entity):
        if entity.properties["file"]:
            w, h = self.source(entity.properties["file"]).size
        else:
            w, h = 32, 32
        box = entity.properties["size"] or (min(w, 96), min(h, 96))
        ratio = min(box[0] / w, box[1] / h)
        return max(1, w * ratio), max(1, h * ratio)

    def bounds(self, entity):
        x, y = entity.properties["position"]
        w, h = self.dimensions(entity)
        return x, y, x + w, y + h

    @staticmethod
    def overlap(a, b, touch=False):
        epsilon = 1e-7 if touch else -1e-7
        return (
            a[0] < b[2] + epsilon
            and a[2] > b[0] - epsilon
            and a[1] < b[3] + epsilon
            and a[3] > b[1] - epsilon
        )

    def emit(self, name, event):
        for callback in list(self.runtime.events.handlers.get((name, event), [])):
            callback()

    def start(self):
        if (
            self.job is not None
            or self.runtime.windows.active is None
            or not self.sprites()
        ):
            return
        self.clock = time.monotonic()

        def pump():
            self.job = None
            if self.runtime.closed:
                return
            now = time.monotonic()
            self.advance(min(0.25, now - self.clock))
            self.clock = now
            self.render()
            if not self.runtime.closed:
                self.job = self.runtime.scheduler.later(1 / 60, pump)

        self.job = self.runtime.scheduler.later(1 / 60, pump)

    def advance(self, seconds):
        if (
            type(seconds) not in (int, float)
            or not math.isfinite(seconds)
            or seconds < 0
        ):
            raise KitleanError("Invalid world delta time", self.runtime.line)
        self.accumulator += seconds
        while self.accumulator + 1e-10 >= 1 / 120:
            self.step(1 / 120)
            self.accumulator -= 1 / 120
            if self.runtime.closed:
                break

    def step(self, dt):
        rt = self.runtime
        menu = rt.windows.active or rt.context
        entities = self.sprites(menu)
        focus = rt.windows.root.focus_get() if rt.windows.root is not None else None
        typing = focus is not None and focus.winfo_class() in (
            "Entry",
            "TEntry",
            "Text",
            "Spinbox",
        )
        for entity in entities:
            if entity.name not in rt.objects or not entity.properties["visible"]:
                continue
            p = entity.properties
            dx = dy = 0.0
            mode = p["setting.move"]
            if mode and not typing:
                up, down, left, right = (
                    ("w", "s", "a", "d")
                    if mode == "wsad"
                    else ("Up", "Down", "Left", "Right")
                )
                dx = float(right in rt.keyboard.down) - float(left in rt.keyboard.down)
                dy = float(down in rt.keyboard.down) - float(up in rt.keyboard.down)
                length = math.hypot(dx, dy)
                if length:
                    dx = dx / length * p["speed"] * dt
                    dy = dy / length * p["speed"] * dt
            entity.grounded = False
            if p["gravity"] > 0:
                entity.velocity = getattr(entity, "velocity", 0.0) + p["gravity"] * dt
                dy += entity.velocity * dt
            for axis, delta in ((0, dx), (1, dy)):
                if not delta:
                    continue
                position = list(p["position"])
                position[axis] += delta
                p["position"] = tuple(position)
                if p["collision"]:
                    for other in entities:
                        if (
                            other is entity
                            or not other.properties["visible"]
                            or not other.properties["collision"]
                        ):
                            continue
                        if self.overlap(self.bounds(entity), self.bounds(other)):
                            a = self.bounds(entity)
                            b = self.bounds(other)
                            w, h = self.dimensions(entity)
                            position[axis] = (
                                (b[axis] - (w if axis == 0 else h))
                                if delta > 0
                                else b[axis + 2]
                            )
                            p["position"] = tuple(position)
                            if axis == 1:
                                entity.velocity = 0.0
                                entity.grounded = delta > 0
                if axis == 1 and p["gravity"] > 0:
                    height = rt.get(entity.parent).properties["size"][1]
                    w, h = self.dimensions(entity)
                    if p["position"][1] + h >= height:
                        p["position"] = (p["position"][0], height - h)
                        entity.velocity = 0.0
                        entity.grounded = True
            animation = getattr(entity, "animation_state", None)
            if animation:
                animation["elapsed"] += dt * p["animation.speed"]
                if animation["elapsed"] >= 1:
                    if p["animation.loop"]:
                        animation["elapsed"] %= 1
                    else:
                        animation["elapsed"] = 1
                        entity.animation_state = None
                    self.emit(entity.name, "animation.finished")
                entity.visual_phase = animation["elapsed"]
                entity.visual_animation = animation["name"]
        pairs = set()
        colliders = [
            e
            for e in entities
            if e.name in rt.objects
            and e.properties["visible"]
            and e.properties["collision"]
        ]
        for i, a in enumerate(colliders):
            for b in colliders[i + 1 :]:
                if self.overlap(self.bounds(a), self.bounds(b), touch=True):
                    pair = tuple(sorted((a.name, b.name)))
                    pairs.add(pair)
                    if pair not in self.contacts:
                        self.emit(a.name, "collided." + b.name)
                        self.emit(b.name, "collided." + a.name)
        self.contacts = pairs

    def action(self, name, action, args):
        rt = self.runtime
        e = rt.get(name)
        p = e.properties
        arities = {
            "hide": 0,
            "show": 0,
            "move": 2,
            "teleport": 2,
            "rotate": 1,
            "jump": 1,
            "animate": 1,
        }
        if action not in arities or len(args) != arities[action]:
            raise KitleanError(
                "Unknown action or wrong number of arguments: " + action, rt.line
            )
        if not e.kind.startswith("item."):
            raise KitleanError("Action requires an item object", rt.line)
        if action in ("hide", "show"):
            rt.set(e.name, "visible", action == "show")
            return
        if action == "animate":
            if e.kind != "item.sprite" or args[0] not in ("bounce", "rotate", "fade"):
                raise KitleanError(
                    "Unsupported sprite animation: " + str(args[0]), rt.line
                )
            e.animation_state = {"name": args[0], "elapsed": 0.0}
            e.visual_animation = args[0]
            e.visual_phase = 0.0
            return
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in args):
            raise KitleanError("Action arguments must be finite numbers", rt.line)
        if action in ("move", "teleport"):
            position = p["position"]
            if position is None:
                position = (
                    (e.widget.winfo_x(), e.widget.winfo_y())
                    if e.widget is not None
                    else (20, 20)
                )
            value = (
                tuple(position[i] + args[i] for i in range(2))
                if action == "move"
                else tuple(args)
            )
            rt.set(e.name, "position", value)
        elif action == "rotate":
            if e.kind not in ("item.sprite", "item.image"):
                raise KitleanError("rotate requires a sprite or image", rt.line)
            rt.set(e.name, "rotation", (p["rotation"] + args[0]) % 360)
        elif action == "jump":
            if e.kind != "item.sprite" or p["gravity"] <= 0 or args[0] <= 0:
                raise KitleanError(
                    "jump requires a sprite, positive gravity and power", rt.line
                )
            if getattr(e, "grounded", False):
                e.velocity = -args[0]
                e.grounded = False

    def random_position(self, e, menu, near=None):
        rt = self.runtime
        gui = rt.get(menu)
        if gui.kind != "gui.menu":
            raise KitleanError("A GUI map is required", rt.line)
        width, height = gui.properties["size"]
        w, h = self.dimensions(e)
        if w > width or h > height:
            raise KitleanError("Object does not fit the map", rt.line)
        for _ in range(100):
            if near:
                x = self.rng.uniform(max(0, near[0] - 96), min(width - w, near[0] + 96))
                y = self.rng.uniform(
                    max(0, near[1] - 96), min(height - h, near[1] + 96)
                )
            else:
                x = self.rng.uniform(0, width - w)
                y = self.rng.uniform(0, height - h)
            box = (x, y, x + w, y + h)
            if all(
                other is e
                or not other.properties["visible"]
                or not other.properties["collision"]
                or not self.overlap(box, self.bounds(other), touch=True)
                for other in self.sprites(menu)
            ):
                return (x, y)
        raise KitleanError(
            "Cannot find a free NPC position after 100 attempts", rt.line
        )

    def save_template(self, e):
        if e.kind != "item.sprite":
            raise KitleanError("NPC templates require a sprite", self.runtime.line)
        self.templates[e.name] = copy.deepcopy(e.properties)
        e.template = True
        self.render()

    def copy(self, name, alias=None, menu=None):
        rt = self.runtime
        source = rt.get(name)
        props = copy.deepcopy(source.properties)
        if source.kind == "gui.menu":
            raise KitleanError("Copy individual items, not a GUI world", rt.line)
        e = rt.create(source.kind, alias or self.unique(source.name + "_copy"))
        e.properties = props
        e.parent = menu or source.parent
        for field in (
            "velocity",
            "grounded",
            "animation_state",
            "visual_animation",
            "visual_phase",
        ):
            if hasattr(source, field):
                setattr(e, field, copy.deepcopy(getattr(source, field)))
        if rt.windows.root is not None:
            rt.windows.build()
        return e

    def summon(self, template, random_mode, target=None, alias=None):
        rt = self.runtime
        if template not in self.templates:
            raise KitleanError(
                "Unknown NPC template: " + template,
                rt.line,
                "Create and save the NPC before summoning it.",
            )
        menu = rt.windows.active or rt.context
        near = None
        position = None
        if isinstance(target, str):
            destination = rt.get(target)
            if destination.kind == "gui.menu":
                menu = destination.name
            elif destination.kind == "item.sprite":
                menu = destination.parent
                near = destination.properties["position"]
            else:
                raise KitleanError(
                    "NPC target must be a map, sprite or coordinates", rt.line
                )
        elif target is not None:
            self.coordinates(target)
            position = tuple(target)
        if menu is None:
            raise KitleanError("No active map for NPC", rt.line)
        name = alias or self.unique(template)
        if name in rt.objects:
            raise KitleanError("Duplicate NPC alias: " + name, rt.line)
        e = rt.create("item.sprite", name)
        e.parent = menu
        e.properties = copy.deepcopy(self.templates[template])
        try:
            if position is None:
                position = self.random_position(e, menu, near)
            else:
                width, height = rt.get(menu).properties["size"]
                w, h = self.dimensions(e)
                if (
                    position[0] < 0
                    or position[1] < 0
                    or position[0] + w > width
                    or position[1] + h > height
                ):
                    raise KitleanError("NPC position is outside the map", rt.line)
                box = (position[0], position[1], position[0] + w, position[1] + h)
                if any(
                    other is not e
                    and other.properties["visible"]
                    and other.properties["collision"]
                    and self.overlap(box, self.bounds(other), touch=True)
                    for other in self.sprites(menu)
                ):
                    raise KitleanError("NPC position is occupied", rt.line)
            e.properties["position"] = position
        except BaseException:
            rt.remove(e.name)
            raise
        self.render()
        return e

    def coordinates(self, value):
        if (
            not isinstance(value, (list, tuple))
            or len(value) != 2
            or any(type(x) not in (int, float) or not math.isfinite(x) for x in value)
        ):
            raise KitleanError("Expected two finite coordinates", self.runtime.line)

    def outof(self, name, menu):
        rt = self.runtime
        e = rt.get(name)
        gui = rt.get(menu)
        if e.kind != "item.sprite" or gui.kind != "gui.menu":
            raise KitleanError("outof requires a sprite and a GUI map", rt.line)
        if e.parent != gui.name:
            return False
        x, y, right, bottom = self.bounds(e)
        width, height = gui.properties["size"]
        direction = (
            (-1, 0)
            if x < 0
            else (1, 0)
            if right > width
            else (0, -1)
            if y < 0
            else (0, 1)
            if bottom > height
            else None
        )
        key = (e.name, gui.name)
        if direction is None:
            self.outside.discard(key)
            return False
        if key in self.outside:
            return False
        self.outside.add(key)
        self.pending[gui.name] = (e.name, direction)
        return True

    def next_segment(self, menu):
        rt = self.runtime
        root = rt.get(menu).name
        if root not in self.pending:
            if root in self.maps:
                return False
            raise KitleanError(
                "No boundary crossing before create " + menu + ".gui.next", rt.line
            )
        if root not in self.maps:
            self.maps[root] = Segments(self, root)
        traveler, direction = self.pending[root]
        self.maps[root].transition(traveler, direction)
        self.pending.pop(root, None)
        self.last_transition = self.maps[root]
        return True

    def camera(self, menu):
        rt = self.runtime
        gui = rt.get(menu)
        p = gui.properties
        zoom = p["camera.zoom"]
        x = y = 0.0
        follow = p["camera.follow"]
        if follow:
            e = rt.get(follow)
            if e.parent == gui.name:
                w, h = self.dimensions(e)
                x = e.properties["position"][0] + w / 2 - p["size"][0] / (2 * zoom)
                y = e.properties["position"][1] + h / 2 - p["size"][1] / (2 * zoom)
        return x, y, zoom

    def screen_position(self, name):
        e = self.runtime.get(name)
        x, y, z = self.camera(e.parent)
        px, py = e.properties["position"]
        return (px - x) * z, (py - y) * z

    def render(self):
        if self.runtime.windows.root is not None:
            self.runtime.windows.render_world()

    def close(self):
        self.runtime.scheduler.cancel(self.job)
        self.job = None
        for world in self.maps.values():
            world.close()
        self.maps.clear()
        self.images.clear()
        self.contacts.clear()
        self.pending.clear()
        self.outside.clear()
