from dataclasses import dataclass, field

DEFAULTS = {
    "gui.menu": (800, 500),
    "item.button": (160, 45),
    "item.input": (240, 40),
    "item.label": None,
    "item.checkbox": None,
}


@dataclass
class Element:
    kind: str
    name: str
    parent: str | None = None
    properties: dict = field(default_factory=dict)
    widget: object = None
    variable: object = None

    def __post_init__(self):
        self.properties.update(
            text="",
            title="Kitlean",
            background="#FFFFFF" if self.kind == "gui.menu" else "#F0F0F0",
            color="#202020",
            visible=True,
            disabled=False,
            size=DEFAULTS[self.kind],
            position=None,
            value=False if self.kind == "item.checkbox" else "",
        )
