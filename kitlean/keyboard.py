from .errors import KitleanError

KEYS = {
    **{chr(x): chr(x).lower() for x in range(65, 91)},
    **{str(x): str(x) for x in range(10)},
    "SPACE": "space",
    "ENTER": "Return",
    "ESCAPE": "Escape",
    "UP": "Up",
    "DOWN": "Down",
    "LEFT": "Left",
    "RIGHT": "Right",
}


class Keyboard:
    def __init__(self, runtime):
        self.runtime = runtime
        self.down = set()
        self.releases = {}

    def canonical(self, name, line):
        if name.upper() not in KEYS:
            raise KitleanError("Nieznany klawisz: " + name, line)
        return KEYS[name.upper()]

    def attach(self, root):
        root.bind("<KeyPress>", self.press, add="+")
        root.bind("<KeyRelease>", self.release, add="+")
        root.bind("<FocusOut>", self.focus_out, add="+")

    def press(self, event):
        key = event.keysym.lower() if len(event.keysym) == 1 else event.keysym
        if key in self.releases:
            self.runtime.windows.root.after_cancel(self.releases.pop(key))
        if key in self.down:
            return
        widget = self.runtime.windows.root.focus_get()
        if widget is not None and widget.winfo_class() in (
            "Entry",
            "TEntry",
            "Text",
            "Spinbox",
        ):
            return
        self.down.add(key)
        for handler in list(self.runtime.events.handlers.get(("key", key), [])):
            handler()

    def release(self, event):
        key = event.keysym.lower() if len(event.keysym) == 1 else event.keysym
        root = self.runtime.windows.root
        if key in self.releases:
            root.after_cancel(self.releases.pop(key))

        def clear():
            self.releases.pop(key, None)
            self.down.discard(key)

        self.releases[key] = root.after_idle(clear)

    def focus_out(self, event):
        if event.widget is self.runtime.windows.root:
            self.down.clear()

    def close(self):
        root = self.runtime.windows.root
        if root is not None:
            for token in self.releases.values():
                root.after_cancel(token)
        self.releases.clear()
        self.down.clear()
