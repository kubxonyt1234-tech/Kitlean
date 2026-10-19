import ast
import operator
from dataclasses import dataclass

from .errors import KitleanError
from .parser import Parser
from .runtime import Runtime


@dataclass
class Function:
    params: list
    body: list
    closure: object


class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise KeyError(name)


class Interpreter:
    def __init__(self, runtime=None, output=print):
        self.runtime = runtime or Runtime()
        self.env = Environment()
        self.output = output
        self.depth = 0
        self.builtins = {"print": output, "len": len, "str": str, "number": float}

    def execute(self, source):
        self.block(Parser(source).parse(), self.env)
        return self.runtime

    def block(self, nodes, env):
        for node in nodes:
            self.runtime.line = node.line
            try:
                self.statement(node, env)
            except KitleanError:
                raise
            except (
                TypeError,
                ValueError,
                ZeroDivisionError,
                IndexError,
                KeyError,
                OverflowError,
                RecursionError,
            ) as e:
                raise KitleanError(
                    "Niepoprawny typ, wartość lub argument: " + str(e), node.line
                ) from None

    def statement(self, n, env):
        rt = self.runtime

        def ev(e):
            return self.evaluate(e.tree, env, e.line)

        a = n.args
        if n.kind == "create":
            name = ev(a[1])
            try:
                env.get(name)
            except (KeyError, TypeError):
                pass
            else:
                raise KitleanError("Nazwa zajęta przez zmienną lub funkcję", n.line)
            rt.create(a[0], name)
        elif n.kind == "property":
            rt.set(a[0], a[1], ev(a[2]))
        elif n.kind == "last_text":
            name = rt.last.get((rt.context, a[0]))
            if name is None:
                raise KitleanError(
                    "Brak ostatniego elementu w bieżącym kontekście", n.line
                )
            rt.set(name, "text", ev(a[1]))
        elif n.kind == "assign":
            if (
                a[0] in rt.objects
                or a[0] in ("true", "false", "null")
                or a[0] in self.builtins
            ):
                raise KitleanError("Nazwa zastrzeżona lub zajęta", n.line)
            env.values[a[0]] = ev(a[1])
        elif n.kind == "function":
            if (
                a[0] in rt.objects
                or a[0] in self.builtins
                or a[0] in ("true", "false", "null")
            ):
                raise KitleanError("Nazwa zastrzeżona lub zajęta", n.line)
            env.values[a[0]] = Function(a[1], n.body, env)
        elif n.kind == "expression":
            ev(a[0])
        elif n.kind == "repeat":
            count = ev(a[0])
            if type(count) is not int or count < 0:
                raise KitleanError("repeat wymaga nieujemnej liczby całkowitej", n.line)
            for _ in range(count):
                self.block(n.body, env)
        elif n.kind == "if":
            tree = a[0].tree
            if isinstance(tree, ast.Attribute) and tree.attr in ("clicked", "hovered"):
                if not isinstance(tree.value, ast.Name):
                    raise KitleanError("Zdarzenie wymaga nazwy obiektu", n.line)
                element = rt.get(tree.value.id)
                if element.kind == "gui.menu":
                    raise KitleanError("Zdarzenie wymaga elementu item", n.line)
                if n.otherwise:
                    raise KitleanError("Zdarzenia nie obsługują else", n.line)
                rt.events.register(
                    element.name, tree.attr, lambda: self.block(n.body, env)
                )
            else:
                self.block(n.body if ev(a[0]) else n.otherwise, env)
        elif n.kind == "run":
            rt.windows.run(ev(a[0]))
        elif n.kind == "close_app":
            rt.windows.close()

    def evaluate(self, n, env, line):
        self.runtime.line = line

        def ev(x):
            return self.evaluate(x, env, line)

        if isinstance(n, ast.Constant):
            if type(n.value) not in (str, int, float, bool, type(None)):
                raise KitleanError("Niedozwolony literał", line)
            return n.value
        if isinstance(n, ast.Name):
            if n.id in ("true", "false", "null"):
                return {"true": True, "false": False, "null": None}[n.id]
            try:
                return env.get(n.id)
            except KeyError:
                raise KitleanError("Nieznany identyfikator: " + n.id, line) from None
        if isinstance(n, (ast.List, ast.Tuple)):
            values = [ev(x) for x in n.elts]
            return tuple(values) if isinstance(n, ast.Tuple) else values
        if isinstance(n, ast.Attribute):
            if not isinstance(n.value, ast.Name):
                raise KitleanError("Niedozwolony dostęp do atrybutu", line)
            return self.runtime.read(n.value.id, n.attr)
        if isinstance(n, ast.BinOp):
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
            }
            return ops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return {
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
                ast.Not: operator.not_,
            }[type(n.op)](ev(n.operand))
        if isinstance(n, ast.BoolOp):
            value = ev(n.values[0])
            for item in n.values[1:]:
                if (
                    isinstance(n.op, ast.And)
                    and not value
                    or isinstance(n.op, ast.Or)
                    and value
                ):
                    return value
                value = ev(item)
            return value
        if isinstance(n, ast.Compare):
            ops = {
                ast.Eq: operator.eq,
                ast.NotEq: operator.ne,
                ast.Lt: operator.lt,
                ast.LtE: operator.le,
                ast.Gt: operator.gt,
                ast.GtE: operator.ge,
                ast.In: lambda a, b: a in b,
                ast.NotIn: lambda a, b: a not in b,
            }
            left = ev(n.left)
            for op, right in zip(n.ops, n.comparators, strict=True):
                right = ev(right)
                if not ops[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(n, ast.Subscript):
            return ev(n.value)[ev(n.slice)]
        if isinstance(n, ast.Call):
            args = [ev(x) for x in n.args]
            if isinstance(n.func, ast.Attribute):
                f = n.func
                if (
                    isinstance(f.value, ast.Attribute)
                    and isinstance(f.value.value, ast.Name)
                    and f.value.attr == "gui"
                    and f.attr == "menu"
                    and f.value.value.id in ("open", "close")
                ):
                    if len(args) != 1 or not isinstance(args[0], str):
                        raise KitleanError("Oczekiwano jednej nazwy menu", line)
                    return (
                        self.runtime.windows.open
                        if f.value.value.id == "open"
                        else self.runtime.windows.hide
                    )(args[0])
                raise KitleanError("Niedozwolone wywołanie", line)
            if not isinstance(n.func, ast.Name):
                raise KitleanError("Niedozwolone wywołanie", line)
            if n.func.id in self.builtins:
                return self.builtins[n.func.id](*args)
            function = ev(n.func)
            if not isinstance(function, Function):
                raise KitleanError("Obiekt nie jest funkcją", line)
            if len(args) != len(function.params):
                raise KitleanError("Niepoprawna liczba argumentów", line)
            if self.depth >= 100:
                raise KitleanError("Przekroczono limit rekurencji (100)", line)
            local = Environment(function.closure)
            local.values.update(zip(function.params, args, strict=True))
            self.depth += 1
            try:
                self.block(function.body, local)
            finally:
                self.depth -= 1
            return None
        raise KitleanError("Niedozwolone wyrażenie", line)
