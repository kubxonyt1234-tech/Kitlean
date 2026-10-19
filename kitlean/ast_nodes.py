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
