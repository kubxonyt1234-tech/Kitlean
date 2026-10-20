import math
from pathlib import Path

from .audio import Audio
from .errors import KitleanError
from .gui.elements import Element
from .gui.events import Events
from .gui.windows import Windows
from .keyboard import Keyboard
from .scheduler import Scheduler
from .storage import Storage
from .world import World


class Runtime:
    def __init__(self):
        self.objects = {}
        self.last = {}
        self.context = None
        self.events = Events()
        self.windows = Windows(self)
        self.line = 1
        self.bindings = {}
        self.dependencies = {}
        self.defaults = {}
        self.program = Path.cwd() / "program.kit"
        self.audio = Audio()
        self.scheduler = Scheduler(self)
        self.keyboard = Keyboard(self)
        self.timers = {}
        self.closed = False
        self.storage = Storage(self.program)
        self.world = World(self)

    def resolve_name(self, name):
        if name in self.objects:
            return name
        if name in self.defaults:
            kind = self.defaults[name]
            if kind == "gui.menu":
                return self.last.get((None, kind))
            if kind in ("audio.music", "timer"):
                return self.last.get((None, kind))
            return self.last.get((self.context, kind))
        return name

    def get(self, name):
        requested = name
        name = self.resolve_name(name)
        if name not in self.objects:
            raise KitleanError(
                "Unknown object: " + str(requested),
                self.line,
                "Create the object before using it.",
            )
        return self.objects[name]

    def create(self, kind, name):
        if (
            not isinstance(name, str)
            or not name.isidentifier()
            or name
            in (
                "true",
                "false",
                "null",
                "print",
                "len",
                "str",
                "number",
                "open",
                "close",
            )
        ):
            raise KitleanError("Niepoprawna nazwa obiektu", self.line)
        if name in self.objects:
            raise KitleanError("Nazwa obiektu już istnieje: " + name, self.line)
        e = Element(kind, name)
        if kind == "gui.menu":
            self.context = name
        elif kind.startswith("item."):
            if self.context is None:
                raise KitleanError("Najpierw utwórz gui.menu", self.line)
            e.parent = self.context
        self.objects[name] = e
        scope = self.context if kind.startswith("item.") else None
        self.last[(scope, kind)] = name
        short = (
            "gui"
            if kind == "gui.menu"
            else "audio"
            if kind == "audio.music"
            else kind.split(".")[-1]
        )
        self.defaults[short] = kind
        if self.windows.root is not None:
            self.windows.build()
            self.world.start()
        return e

    def read(self, name, prop):
        if name == "mouse" and prop == "position":
            return self.world.mouse
        e = self.get(name)
        if prop == "last" and e.kind == "gui.menu":
            manager = self.world.maps.get(e.name)
            return manager.previous if manager else None
        self.validate_property(e, prop)
        if prop == "parent":
            return e.parent
        if prop == "value" and e.variable is not None:
            return e.variable.get()
        return e.properties[prop]

    def validate_property(self, e, prop):
        if e.kind == "audio.music":
            if prop not in ("file", "volume", "loop"):
                raise KitleanError("Nieznana właściwość audio: " + prop, self.line)
            return
        if e.kind == "timer":
            if prop not in ("interval", "loop"):
                raise KitleanError("Nieznana właściwość timera: " + prop, self.line)
            return
        common = {
            "background",
            "size",
            "position",
            "visible",
            "disabled",
            "margin",
            "align",
            "rounded",
        }
        allowed = common | (
            {"title", "fullscreen", "camera.follow", "camera.zoom"}
            if e.kind == "gui.menu"
            else {"text", "color", "parent"}
        )
        if e.kind in ("item.image", "item.sprite"):
            allowed.update(("file", "rotation"))
        if e.kind == "item.sprite":
            allowed.update(
                (
                    "speed",
                    "gravity",
                    "collision",
                    "setting.move",
                    "animation.speed",
                    "animation.loop",
                    "save",
                )
            )
        if e.kind in ("item.input", "item.checkbox"):
            allowed.add("value")
        if prop not in allowed:
            raise KitleanError("Nieznana właściwość: " + prop, self.line)

    def render_template(self, template, env, line, owners=None):
        result = []
        for variable, value in template.parts:
            if variable:
                try:
                    value = (owners[value] if owners is not None else env).get(value)
                except KeyError:
                    raise KitleanError(
                        "Nieistniejąca zmienna w interpolacji: " + value, line
                    ) from None
                if value is True:
                    value = "true"
                elif value is False:
                    value = "false"
                elif value is None:
                    value = "null"
                else:
                    value = str(value)
            result.append(value)
        return "".join(result)

    def unbind(self, key):
        previous = self.bindings.pop(key, None)
        if previous:
            for dependency in previous[3]:
                keys = self.dependencies.get(dependency)
                if keys is not None:
                    keys.discard(key)
                    if not keys:
                        self.dependencies.pop(dependency)

    def bind_text(self, name, prop, template, env, line):
        value = self.render_template(template, env, line)
        dependencies = {
            (env.resolve(variable), variable) for variable in template.dependencies
        }
        self.set(name, prop, value)
        key = (self.get(name).name, prop)
        self.bindings[key] = (template, env, line, dependencies)
        for dependency in dependencies:
            self.dependencies.setdefault(dependency, set()).add(key)

    def variable_changed(self, owner, name):
        for key in tuple(self.dependencies.get((owner, name), ())):
            template, env, line, dependencies = self.bindings[key]
            owners = {variable: scope for scope, variable in dependencies}
            value = self.render_template(template, env, line, owners)
            self.set(*key, value, keep_binding=True)

    def set(self, name, prop, value, keep_binding=False):
        e = self.get(name)
        name = e.name
        self.validate_property(e, prop)
        if prop == "save":
            if value != "npc":
                raise KitleanError("Use sprite.save=npc", self.line)
            self.world.save_template(e)
            return
        if prop == "position" and value == "random":
            if e.kind != "item.sprite":
                raise KitleanError("Random positioning requires a sprite", self.line)
            value = self.world.random_position(e, e.parent)
        if prop in (
            "speed",
            "gravity",
            "rotation",
            "animation.speed",
            "camera.zoom",
            "margin",
            "rounded",
        ):
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or value < 0
                or prop in ("animation.speed", "camera.zoom")
                and value == 0
            ):
                raise KitleanError("Invalid numeric property: " + prop, self.line)
        if prop == "align" and value not in ("left", "center", "right"):
            raise KitleanError("align must be left, center or right", self.line)
        if (
            prop in ("fullscreen", "collision", "animation.loop")
            and type(value) is not bool
        ):
            raise KitleanError(prop + " requires boolean", self.line)
        if prop == "camera.follow":
            target = self.get(value)
            if target.kind != "item.sprite" or target.parent != e.name:
                raise KitleanError(
                    "camera.follow requires a sprite in this GUI", self.line
                )
            value = target.name
        if prop == "setting.move" and value not in ("wsad", "arrows"):
            raise KitleanError("Unknown movement mode", self.line)
        if prop == "file":
            if not isinstance(value, str) or not value:
                raise KitleanError("file wymaga ścieżki tekstowej", self.line)
            if not self.asset_path(value).is_file():
                raise KitleanError(
                    "Brak pliku: " + str(self.asset_path(value)), self.line
                )
        if prop in ("volume", "interval"):
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or (not 0 <= value <= 100 if prop == "volume" else value <= 0)
            ):
                raise KitleanError("Nieprawidłowa wartość " + prop, self.line)
        if prop == "loop" and type(value) is not bool:
            raise KitleanError("loop wymaga boolean", self.line)
        if prop in (
            "text",
            "title",
            "background",
            "color",
            "parent",
        ) and not isinstance(value, str):
            raise KitleanError("Wymagany tekst: " + prop, self.line)
        if prop in ("visible", "disabled") and type(value) is not bool:
            raise KitleanError("Wymagana wartość boolean", self.line)
        if prop == "size":
            if (
                not isinstance(value, (tuple, list))
                or len(value) != 2
                or any(type(v) is not int or v <= 0 for v in value)
            ):
                raise KitleanError(
                    "Wymagana para dodatnich liczb całkowitych: size", self.line
                )
        if prop == "position":
            self.world.coordinates(value)
        if prop == "value" and (
            type(value) is not bool
            if e.kind == "item.checkbox"
            else not isinstance(value, str)
        ):
            raise KitleanError("Niepoprawny typ value", self.line)
        if not keep_binding:
            self.unbind((name, prop))
        if prop == "parent":
            parent = self.get(value)
            if parent.kind != "gui.menu":
                raise KitleanError("Rodzic musi być gui.menu", self.line)
            old_parent = e.parent
            e.parent = parent.name
            if (
                old_parent != parent.name
                and self.last.get((old_parent, e.kind)) == e.name
            ):
                candidates = [
                    item.name
                    for item in self.objects.values()
                    if item.parent == old_parent and item.kind == e.kind
                ]
                if candidates:
                    self.last[(old_parent, e.kind)] = candidates[-1]
                else:
                    self.last.pop((old_parent, e.kind), None)
            self.context = parent.name
            self.last[(parent.name, e.kind)] = e.name
        else:
            if e.kind == "item.input" and prop == "text":
                e.properties["value"] = value
                if e.variable is not None:
                    e.variable.set(value)
            e.properties[prop] = value
            if prop == "value" and e.variable is not None:
                e.variable.set(value)
        if e.kind == "audio.music":
            self.audio.change(e, prop)
            return
        if e.kind == "timer":
            return
        if e.kind == "item.sprite":
            if self.windows.root is not None:
                self.world.start()
                self.world.render()
            return
        if self.windows.root is not None:
            if prop in ("text", "title", "value"):
                self.windows.update_text(e, prop)
            else:
                self.windows.build()

    def configure_program(self, program, data_root=None):
        self.program = Path(program).resolve()
        self.storage = Storage(self.program, data_root)

    def asset_path(self, value):
        path = Path(value)
        return path if path.is_absolute() else self.program.parent / path

    def start_timer(self, element):
        if element.name in self.timers:
            return

        def tick():
            self.timers.pop(element.name, None)
            if element.properties["loop"]:
                self.timers[element.name] = self.scheduler.later(
                    element.properties["interval"], tick
                )
            self.events.emit(element, "tick")

        self.timers[element.name] = self.scheduler.later(
            element.properties["interval"], tick
        )

    def stop_timer(self, element):
        self.scheduler.cancel(self.timers.pop(element.name, None))

    def cleanup(self):
        self.closed = True
        self.scheduler.close()
        self.timers.clear()
        self.keyboard.close()
        self.audio.close()
        self.world.close()

    def remove(self, name, suspend=False):
        e = self.get(name)
        name = e.name
        if e.kind == "gui.menu":
            raise KitleanError(
                "Cannot delete a GUI world; delete individual objects", self.line
            )
        if e.kind == "audio.music":
            entry = self.audio.items.pop(name, None)
            if entry:
                entry[2].stop()
        if e.kind == "timer":
            self.stop_timer(e)
        for key in list(self.bindings):
            if key[0] == name:
                self.unbind(key)
        for key in list(self.events.handlers):
            if key[0] == name or not suspend and key[1] == "collided." + name:
                self.events.handlers.pop(key, None)
        self.events.registered = {
            key
            for key in self.events.registered
            if key[0] != name and (suspend or key[1] != "collided." + name)
        }
        for key, value in list(self.last.items()):
            if value == name:
                candidates = [
                    item.name
                    for item in self.objects.values()
                    if item.name != name
                    and item.kind == key[1]
                    and (key[0] is None or item.parent == key[0])
                ]
                if candidates:
                    self.last[key] = candidates[-1]
                else:
                    self.last.pop(key, None)
        if e.widget is not None:
            e.widget.destroy()
        self.objects.pop(name)
        self.world.contacts = {pair for pair in self.world.contacts if name not in pair}
        self.world.outside = {key for key in self.world.outside if key[0] != name}
        self.world.pending = {
            key: value for key, value in self.world.pending.items() if value[0] != name
        }
        self.world.render()
