import ast

from .ast_nodes import Expression
from .errors import KitleanError


class MathCall(ast.expr):
    _fields = ("args",)

    def __init__(self, name, args):
        self.name, self.args = name, args


class Expressions:
    """Pratt parser wyrażeń Kitlean. Dwukropek ma priorytet mnożenia."""

    OPS = {
        "or": (10, ast.Or),
        "and": (20, ast.And),
        "+": (40, ast.Add),
        "-": (40, ast.Sub),
        "*": (50, ast.Mult),
        ":": (50, ast.Div),
        "/": (50, ast.Div),
        "//": (50, ast.FloorDiv),
        "%": (50, ast.Mod),
        "**": (70, ast.Pow),
    }
    CMP = {
        "==": ast.Eq,
        "!=": ast.NotEq,
        "<": ast.Lt,
        "<=": ast.LtE,
        ">": ast.Gt,
        ">=": ast.GtE,
        "in": ast.In,
        "not in": ast.NotIn,
    }

    def __init__(self, tokens, templates, line):
        self.tokens = tokens
        self.templates = templates
        self.line = line
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos].value if self.pos < len(self.tokens) else ""

    def take(self, value=None):
        if not self.peek() or value is not None and self.peek() != value:
            self.fail()
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def fail(self):
        raise KitleanError(
            "Niepoprawne wyrażenie Kitlean przy: " + (self.peek() or "końcu linii"),
            self.line,
        )

    def parse(self):
        tree = self.expr()
        if self.pos != len(self.tokens):
            self.fail()
        return Expression(tree, self.line)

    def expr(self, minimum=0):
        t = self.take()
        v = t.value
        if v in ("+", "-", "not"):
            left = ast.UnaryOp(
                {"-": ast.USub, "+": ast.UAdd, "not": ast.Not}[v](),
                self.expr(25 if v == "not" else 65),
            )
        elif v == "(":
            left = self.sequence(")", tuple_mode=True)
        elif v == "[":
            left = ast.List(self.items("]"), ast.Load())
        elif v in self.templates:
            left = self.templates[v]
        elif t.kind in ("STRING", "NUMBER"):
            try:
                left = ast.Constant(ast.literal_eval(v))
            except (ValueError, SyntaxError):
                self.fail()
        elif t.kind == "NAME":
            if v == "math" and self.peek() == "/":
                self.take("/")
                name = self.take()
                if name.kind != "NAME":
                    self.fail()
                self.take("(")
                left = MathCall(name.value, self.items(")"))
            else:
                left = ast.Name(v, ast.Load())
        else:
            self.fail()
        while True:
            v = self.peek()
            if v in (".", "(", "[") and 90 >= minimum:
                self.take()
                if v == ".":
                    name = self.take()
                    if name.kind != "NAME":
                        self.fail()
                    left = ast.Attribute(left, name.value, ast.Load())
                elif v == "(":
                    left = ast.Call(left, self.items(")"), [])
                else:
                    index = self.expr()
                    self.take("]")
                    left = ast.Subscript(left, index, ast.Load())
                continue
            comparison = v
            if (
                v == "not"
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].value == "in"
            ):
                comparison = "not in"
            if comparison in self.CMP and 30 >= minimum:
                ops = []
                rights = []
                while comparison in self.CMP:
                    self.take()
                    if comparison == "not in":
                        self.take("in")
                    ops.append(self.CMP[comparison]())
                    rights.append(self.expr(31))
                    comparison = self.peek()
                    if (
                        comparison == "not"
                        and self.pos + 1 < len(self.tokens)
                        and self.tokens[self.pos + 1].value == "in"
                    ):
                        comparison = "not in"
                left = ast.Compare(left, ops, rights)
                continue
            if v not in self.OPS or self.OPS[v][0] < minimum:
                break
            precedence, op = self.OPS[v]
            self.take()
            right = self.expr(precedence if v == "**" else precedence + 1)
            left = (
                ast.BoolOp(op(), [left, right])
                if v in ("and", "or")
                else ast.BinOp(left, op(), right)
            )
        return left

    def items(self, end):
        result = []
        if self.peek() != end:
            while True:
                result.append(self.expr())
                if self.peek() != ",":
                    break
                self.take(",")
                if self.peek() == end:
                    break
        self.take(end)
        return result

    def sequence(self, end, tuple_mode=False):
        if self.peek() == end:
            self.take(end)
            return ast.Tuple([], ast.Load())
        first = self.expr()
        if self.peek() != ",":
            self.take(end)
            return first
        self.take(",")
        return ast.Tuple([first] + self.items(end), ast.Load())
