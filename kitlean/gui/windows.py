import tkinter as tk

from ..errors import KitleanError
from .layout import arrange


class Windows:
    def __init__(self, runtime):
        self.runtime = runtime
        self.root = None
        self.active = None
        self.running = False
        self.error = None

    def ensure(self):
        if self.root is None:
            try:
                self.root = tk.Tk()
                self.root.withdraw()
                self.root.report_callback_exception = self.callback_error
                self.root.protocol("WM_DELETE_WINDOW", self.close)
            except tk.TclError as e:
                raise KitleanError("Nie można uruchomić tkinter: " + str(e)) from None

    def callback_error(self, typ, value, tb):
        self.error = (
            value if isinstance(value, KitleanError) else KitleanError(str(value))
        )
        self.close()

    def build(self):
        self.ensure()
        rt = self.runtime
        for element in rt.objects.values():
            if element.kind == "gui.menu" and element.widget is None:
                element.widget = tk.Frame(self.root)
        for element in rt.objects.values():
            if element.kind == "gui.menu":
                continue
            parent = rt.get(element.parent)
            if element.widget is not None and str(element.widget.master) == str(
                parent.widget
            ):
                continue
            if element.widget is not None:
                if element.variable is not None:
                    element.properties["value"] = element.variable.get()
                element.widget.destroy()
            master = parent.widget
            if element.kind == "item.button":
                element.widget = tk.Button(
                    master, command=lambda e=element: rt.events.emit(e, "clicked")
                )
            elif element.kind == "item.label":
                element.widget = tk.Label(master)
            elif element.kind == "item.input":
                element.variable = tk.StringVar(
                    master, value=element.properties["value"]
                )
                element.widget = tk.Entry(master, textvariable=element.variable)
            else:
                element.variable = tk.BooleanVar(
                    master, value=element.properties["value"]
                )
                element.widget = tk.Checkbutton(
                    master,
                    variable=element.variable,
                    command=lambda e=element: rt.events.emit(e, "clicked"),
                )
            element.widget.bind(
                "<Enter>", lambda event, e=element: rt.events.emit(e, "hovered")
            )
            if element.kind in ("item.label", "item.input"):
                element.widget.bind(
                    "<Button-1>", lambda event, e=element: rt.events.emit(e, "clicked")
                )
        self.refresh()

    def update_text(self, element, prop):
        """Odświeża istniejący widget; nie tworzy okien ani nowych callbacków."""
        if element.kind == "gui.menu":
            if self.active == element.name and prop == "title":
                self.root.title(element.properties["title"])
        elif element.widget is not None:
            if prop == "text" and element.kind != "item.input":
                element.widget.configure(text=element.properties["text"])
            self.layout_menu(element.parent)

    def layout_menu(self, name):
        if self.root is None:
            return
        self.root.update_idletasks()
        children = [
            e
            for e in self.runtime.objects.values()
            if e.parent == name and e.widget is not None
        ]
        positions = arrange(children)
        for e in children:
            if e.name not in positions:
                e.widget.place_forget()
                continue
            x, y = positions[e.name]
            kwargs = {"x": x, "y": y}
            if e.properties["size"]:
                kwargs.update(
                    zip(("width", "height"), e.properties["size"], strict=True)
                )
            e.widget.place(**kwargs)

    def refresh(self):
        if self.root is None:
            return
        for e in self.runtime.objects.values():
            if e.widget is None:
                continue
            p = e.properties
            try:
                e.widget.configure(background=p["background"])
                if e.kind != "gui.menu":
                    e.widget.configure(fg=p["color"])
                    if e.kind != "item.label":
                        e.widget.configure(
                            state="disabled" if p["disabled"] else "normal"
                        )
                    if e.kind != "item.input":
                        e.widget.configure(text=p["text"])
            except tk.TclError as exc:
                raise KitleanError(
                    "Niepoprawna właściwość GUI: " + str(exc), self.runtime.line
                ) from None
        self.root.update_idletasks()
        for menu in self.runtime.objects.values():
            if menu.kind != "gui.menu":
                continue
            children = [
                e for e in self.runtime.objects.values() if e.parent == menu.name
            ]
            positions = arrange(children)
            for e in children:
                e.widget.place_forget()
                if e.name in positions:
                    x, y = positions[e.name]
                    kwargs = {"x": x, "y": y}
                    if e.properties["size"]:
                        kwargs.update(
                            zip(("width", "height"), e.properties["size"], strict=True)
                        )
                    e.widget.place(**kwargs)
        if self.active:
            p = self.runtime.get(self.active).properties
            self.root.title(p["title"])
            self.root.geometry(f"{p['size'][0]}x{p['size'][1]}")

    def open(self, name):
        menu = self.runtime.get(name)
        if menu.kind != "gui.menu":
            raise KitleanError("Oczekiwano gui.menu", self.runtime.line)
        self.build()
        for e in self.runtime.objects.values():
            if e.kind == "gui.menu":
                e.widget.pack_forget()
        menu.widget.pack(fill="both", expand=True)
        self.active = name
        self.refresh()
        self.root.deiconify()

    def hide(self, name):
        menu = self.runtime.get(name)
        if menu.kind != "gui.menu":
            raise KitleanError("Oczekiwano gui.menu", self.runtime.line)
        if self.active == name:
            self.root.withdraw()
            self.active = None

    def run(self, name):
        if self.running:
            raise KitleanError("Pętla GUI jest już uruchomiona", self.runtime.line)
        self.error = None
        self.open(name)
        self.running = True
        try:
            self.root.mainloop()
        finally:
            self.running = False
        if self.error:
            raise self.error

    def close(self):
        if self.root is not None:
            for e in self.runtime.objects.values():
                if e.variable is not None:
                    e.properties["value"] = e.variable.get()
                    e.variable = None
            self.root.destroy()
            self.root = None
            for e in self.runtime.objects.values():
                e.widget = None
        self.active = None
