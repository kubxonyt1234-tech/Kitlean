"""Canvas-backed button retaining the small tkinter Button API used by Kitlean."""

import tkinter as tk

from PIL import Image, ImageDraw, ImageTk


class RoundedButton(tk.Canvas):
    def __init__(self, master, command=None, **kwargs):
        self.options = {
            "text": "",
            "background": "#F0F0F0",
            "fg": "#202020",
            "state": "normal",
            "rounded": 0,
        }
        self.command = command
        self.picture = None
        super().__init__(
            master, width=160, height=45, highlightthickness=0, takefocus=True
        )
        self.bind("<Configure>", lambda event: self.draw())
        self.bind("<ButtonRelease-1>", lambda event: self.invoke())
        self.bind("<space>", lambda event: self.invoke())
        self.bind("<Return>", lambda event: self.invoke())
        self.configure(**kwargs)

    def configure(self, cnf=None, **kwargs):
        if isinstance(cnf, dict):
            kwargs.update(cnf)
        if not kwargs:
            return super().configure()
        for name in tuple(kwargs):
            canonical = (
                "background" if name == "bg" else "fg" if name == "foreground" else name
            )
            if canonical in self.options:
                self.options[canonical] = kwargs.pop(name)
        if kwargs:
            super().configure(**kwargs)
        self.draw()

    config = configure

    def cget(self, key):
        key = {"bg": "background", "foreground": "fg"}.get(key, key)
        return self.options[key] if key in self.options else super().cget(key)

    def __getitem__(self, key):
        return self.cget(key)

    def invoke(self):
        if self.options["state"] != "disabled" and self.command:
            return self.command()

    def draw(self):
        if not self.winfo_exists():
            return
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())
        try:
            parent = self.master.cget("background")
        except tk.TclError:
            parent = "#FFFFFF"
        super().configure(background=parent)
        background = self.options["background"]
        rgb = self.winfo_rgb(background)
        color = tuple(v // 256 for v in rgb)
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ImageDraw.Draw(image).rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=min(self.options["rounded"], width / 2, height / 2),
            fill=color,
        )
        self.picture = ImageTk.PhotoImage(image, master=self)
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self.picture)
        self.create_text(
            width / 2,
            height / 2,
            text=self.options["text"],
            fill=self.options["fg"]
            if self.options["state"] != "disabled"
            else "#777777",
        )
