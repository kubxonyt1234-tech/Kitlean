from .errors import KitleanError
from .gui.elements import Element
from .gui.events import Events
from .gui.windows import Windows


class Runtime:
    def __init__(self):
        self.objects = {}
        self.last = {}
        self.context = None
        self.events = Events()
        self.windows = Windows(self)
        self.line = 1

    def get(self, name):
        if name not in self.objects:
            raise KitleanError(
                "Unknown object: " + str(name),
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
        else:
            if self.context is None:
                raise KitleanError("Najpierw utwórz gui.menu", self.line)
            e.parent = self.context
        self.objects[name] = e
        self.last[(self.context, kind)] = name
        return e

    def read(self, name, prop):
        e = self.get(name)
        self.validate_property(e, prop)
        if prop == "parent":
            return e.parent
        if prop == "value" and e.variable is not None:
            return e.variable.get()
        return e.properties[prop]

    def validate_property(self, e, prop):
        common = {"background", "size", "position", "visible", "disabled"}
        allowed = common | (
            {"title"} if e.kind == "gui.menu" else {"text", "color", "parent"}
        )
        if e.kind in ("item.input", "item.checkbox"):
            allowed.add("value")
        if prop not in allowed:
            raise KitleanError("Nieznana właściwość: " + prop, self.line)

    def set(self, name, prop, value):
        e = self.get(name)
        self.validate_property(e, prop)
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
        if prop in ("size", "position"):
            if (
                not isinstance(value, (tuple, list))
                or len(value) != 2
                or any(
                    type(v) is not int or v < (1 if prop == "size" else 0)
                    for v in value
                )
            ):
                raise KitleanError(
                    "Wymagana para liczb całkowitych: " + prop, self.line
                )
        if prop == "value" and (
            type(value) is not bool
            if e.kind == "item.checkbox"
            else not isinstance(value, str)
        ):
            raise KitleanError("Niepoprawny typ value", self.line)
        if prop == "parent":
            parent = self.get(value)
            if parent.kind != "gui.menu":
                raise KitleanError("Rodzic musi być gui.menu", self.line)
            e.parent = value
            self.context = value
            self.last[(value, e.kind)] = e.name
        else:
            if e.kind == "item.input" and prop == "text":
                e.properties["value"] = value
                if e.variable is not None:
                    e.variable.set(value)
            e.properties[prop] = value
            if prop == "value" and e.variable is not None:
                e.variable.set(value)
        if self.windows.root is not None:
            self.windows.build()
