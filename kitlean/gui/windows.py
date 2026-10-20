import math
import tkinter as tk

from ..errors import KitleanError
from .button import RoundedButton
from .layout import arrange


class Windows:
    def __init__(self, runtime):
        self.runtime = runtime
        self.root = None
        self.active = None
        self.running = False
        self.error = None
        self.canvases = {}
        self.canvas_items = {}

    def ensure(self):
        if self.root is None:
            try:
                self.root = tk.Tk()
                self.root.withdraw()
                self.root.report_callback_exception = self.callback_error
                self.root.protocol("WM_DELETE_WINDOW", self.close)
                self.runtime.keyboard.attach(self.root)
                self.root.bind("<Motion>", self.mouse_motion, add="+")
                self.root.bind(
                    "<Button-1>", lambda event: self.mouse_click(event, "left"), add="+"
                )
                self.root.bind(
                    "<Button-3>",
                    lambda event: self.mouse_click(event, "right"),
                    add="+",
                )
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
                element.widget.bind(
                    "<Configure>", lambda event, e=element: self.resize_menu(e)
                )
        for element in rt.objects.values():
            if not element.kind.startswith("item.") or element.kind == "item.sprite":
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
                element.widget = RoundedButton(
                    master, command=lambda e=element: rt.events.emit(e, "clicked")
                )
            elif element.kind in ("item.label", "item.image"):
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
            if element.kind in ("item.label", "item.input", "item.image"):
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
            if e.parent == name and e.widget is not None and e.kind != "item.sprite"
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
                if e.kind == "item.image":
                    self.load_image(e)
                e.widget.configure(background=p["background"])
                if e.kind != "gui.menu":
                    e.widget.configure(fg=p["color"])
                    if e.kind not in ("item.label", "item.image"):
                        e.widget.configure(
                            state="disabled" if p["disabled"] else "normal"
                        )
                    if e.kind != "item.input":
                        e.widget.configure(text=p["text"])
                    if e.kind == "item.button":
                        e.widget.configure(rounded=p["rounded"])
            except tk.TclError as exc:
                raise KitleanError(
                    "Niepoprawna właściwość GUI: " + str(exc), self.runtime.line
                ) from None
        self.root.update_idletasks()
        for menu in self.runtime.objects.values():
            if menu.kind != "gui.menu":
                continue
            children = [
                e
                for e in self.runtime.objects.values()
                if e.parent == menu.name
                and e.kind != "item.sprite"
                and e.widget is not None
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
            self.root.attributes("-fullscreen", p["fullscreen"])
        self.render_world()

    def open(self, name):
        menu = self.runtime.get(name)
        if menu.kind != "gui.menu":
            raise KitleanError("Oczekiwano gui.menu", self.runtime.line)
        self.build()
        for e in self.runtime.objects.values():
            if e.kind == "gui.menu":
                e.widget.pack_forget()
        menu.widget.pack(fill="both", expand=True)
        self.active = menu.name
        self.refresh()
        self.root.deiconify()
        self.root.after_idle(self.root.focus_set)
        self.runtime.world.start()

    def hide(self, name):
        menu = self.runtime.get(name)
        if menu.kind != "gui.menu":
            raise KitleanError("Oczekiwano gui.menu", self.runtime.line)
        if self.active == name:
            self.root.withdraw()
            self.active = None

    def load_image(self, element):
        from PIL import Image, ImageOps, ImageTk

        value = element.properties["file"]
        if not value:
            return
        parent = self.runtime.get(element.parent)
        width, height = parent.properties["size"]
        box = element.properties["size"] or (
            min(320, max(1, width - 40)),
            min(240, max(1, height - 40)),
        )
        path = self.runtime.asset_path(value)
        signature = (str(path), box, element.properties["rotation"])
        if getattr(element, "image_key", None) == signature:
            return
        try:
            with Image.open(path) as source:
                picture = ImageOps.exif_transpose(source).convert("RGBA")
                picture.thumbnail(box, Image.Resampling.LANCZOS)
                if element.properties["rotation"]:
                    picture = picture.rotate(
                        -element.properties["rotation"],
                        expand=True,
                        resample=Image.Resampling.BICUBIC,
                    )
                element.image = ImageTk.PhotoImage(picture, master=self.root)
            element.widget.configure(image=element.image)
            element.image_key = signature
        except (OSError, ValueError) as error:
            raise KitleanError(
                "Nie można wczytać obrazka: " + str(error), self.runtime.line
            ) from None

    def run(self, name):
        self.open(name)
        self.loop()

    def loop(self):
        if self.running:
            raise KitleanError("Pętla GUI jest już uruchomiona", self.runtime.line)
        self.running = True
        try:
            self.root.mainloop()
        finally:
            self.running = False
        if self.error:
            raise self.error

    def close(self):
        self.runtime.cleanup()
        if self.root is not None:
            for e in self.runtime.objects.values():
                if e.variable is not None:
                    e.properties["value"] = e.variable.get()
                    e.variable = None
            self.root.destroy()
            self.root = None
            for e in self.runtime.objects.values():
                e.widget = None
                e.image_key = None
        self.active = None
        self.canvases.clear()
        self.canvas_items.clear()

    def resize_menu(self, menu):
        if self.root is None:
            return
        self.layout_menu(menu.name)
        self.render_world()

    def mouse_motion(self, event):
        self.runtime.world.mouse = (
            event.x_root - self.root.winfo_rootx(),
            event.y_root - self.root.winfo_rooty(),
        )

    def mouse_click(self, event, button):
        self.mouse_motion(event)
        self.runtime.world.emit("mouse", button + ".clicked")

    def render_world(self):
        if self.root is None:
            return
        from PIL import Image, ImageTk

        rt = self.runtime
        world = rt.world
        for menu in tuple(rt.objects.values()):
            if menu.kind != "gui.menu" or menu.widget is None:
                continue
            sprites = world.sprites(menu.name)
            if not sprites and menu.name not in self.canvases:
                continue
            if menu.name not in self.canvases:
                canvas = tk.Canvas(menu.widget, highlightthickness=0)
                canvas.place(x=0, y=0, relwidth=1, relheight=1)
                self.canvases[menu.name] = canvas
                self.canvas_items[menu.name] = {}
                for item in rt.objects.values():
                    if item.parent == menu.name and item.widget is not None:
                        tk.Misc.tkraise(item.widget)
            canvas = self.canvases[menu.name]
            items = self.canvas_items[menu.name]
            canvas.configure(background=menu.properties["background"])
            visible = {
                e.name
                for e in sprites
                if e.properties["visible"] and e.properties["file"]
            }
            for name in set(items) - visible:
                canvas.delete(items.pop(name))
            for e in sprites:
                if e.name not in visible:
                    continue
                width, height = world.dimensions(e)
                x, y = world.screen_position(e.name)
                zoom = menu.properties["camera.zoom"]
                phase = getattr(e, "visual_phase", 0)
                animation = getattr(e, "visual_animation", None)
                angle = e.properties["rotation"] + (
                    360 * phase if animation == "rotate" else 0
                )
                offset = -12 * math.sin(phase * math.pi) if animation == "bounce" else 0
                alpha = max(0, 1 - phase) if animation == "fade" else 1
                signature = (
                    e.properties["file"],
                    round(width * zoom),
                    round(height * zoom),
                    round(angle, 2),
                    round(alpha, 3),
                )
                if getattr(e, "world_image_key", None) != signature:
                    picture = world.source(e.properties["file"]).resize(
                        (max(1, round(width * zoom)), max(1, round(height * zoom))),
                        Image.Resampling.LANCZOS,
                    )
                    if angle:
                        picture = picture.rotate(
                            -angle, expand=True, resample=Image.Resampling.BICUBIC
                        )
                    if alpha != 1:
                        picture.putalpha(
                            picture.getchannel("A").point(
                                lambda value, opacity=alpha: int(value * opacity)
                            )
                        )
                    e.world_photo = ImageTk.PhotoImage(picture, master=self.root)
                    e.world_image_key = signature
                if e.name not in items:
                    items[e.name] = canvas.create_image(
                        0, 0, anchor="center", tags=(e.name,)
                    )
                    canvas.tag_bind(
                        e.name,
                        "<Button-1>",
                        lambda event, name=e.name: rt.events.emit(
                            rt.get(name), "clicked"
                        ),
                    )
                    canvas.tag_bind(
                        e.name,
                        "<Enter>",
                        lambda event, name=e.name: rt.events.emit(
                            rt.get(name), "hovered"
                        ),
                    )
                canvas.itemconfigure(items[e.name], image=e.world_photo)
                canvas.coords(
                    items[e.name],
                    x + width * zoom / 2,
                    y + (height / 2 + offset) * zoom,
                )
