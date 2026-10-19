import ast
from dataclasses import dataclass, field


@dataclass
class Statement:
    kind: str
    line: int
    args: tuple = ()
    body: list = field(default_factory=list)
    otherwise: list = field(default_factory=list)


@dataclass
class Expression:
    tree: ast.AST
    line: int


class Template(ast.expr):
    """Literalne fragmenty tekstu i nazwy zmiennych; bez wykonywalnego kodu."""

    _fields = ()

    def __init__(self, parts, line):
        self.parts = parts
        self.line = line

    @property
    def dependencies(self):
        return {value for variable, value in self.parts if variable}
