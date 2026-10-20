import ast
import operator
from dataclasses import dataclass

from .ast_nodes import Template
from .errors import KitleanError, KitleanMathError
from .expressions import MathCall
from .mathematics import calculate
from .parser import Parser
from .runtime import Runtime
from .scheduler import Delay, GuiWait


@dataclass
class Function:
    params: list
    body: list
    closure: object


class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def resolve(self, name):
        if name in self.values:
            return self
        if self.parent:
            return self.parent.resolve(name)
        raise KeyError(name)

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
        self.runtime.closed = False
        self.runtime.scheduler.submit(self.block(Parser(source).parse(), self.env))
        if not self.runtime.windows.running and (
            self.runtime.scheduler.want_loop
            or any(
                token != self.runtime.world.job for token in self.runtime.scheduler.jobs
            )
        ):
            self.runtime.windows.loop()
        return self.runtime

    async def block(self, nodes, env):
        previous_success = False
        transition = None
        for node in nodes:
            if self.runtime.closed:
                return
            self.runtime.line = node.line
            try:
                if node.kind == "thene":
                    if not previous_success:
                        continue
                    operation = node.args[0]
                    if (
                        operation.kind == "summon"
                        and transition is not None
                        and transition.restored
                    ):
                        continue
                    result = await self.statement(operation, env)
                else:
                    transition = None
                    result = await self.statement(node, env)
                previous_success = result is not False
                if (
                    node.kind == "next_segment"
                    or node.kind == "thene"
                    and node.args[0].kind == "next_segment"
                ):
                    transition = self.runtime.world.last_transition
            except ZeroDivisionError:
                raise KitleanMathError("Dzielenie przez zero", node.line) from None
            except KitleanError:
                raise
            except (
                TypeError,
                ValueError,
                IndexError,
                KeyError,
                OverflowError,
                RecursionError,
            ) as e:
                raise KitleanError(
                    "Niepoprawny typ, wartość lub argument: " + str(e), node.line
                ) from None

    async def statement(self, n, env):
        rt = self.runtime

        async def ev(e):
            return await self.evaluate(e.tree, env, e.line)

        a = n.args
        if n.kind == "create":
            if a[1] is None:
                number = len(rt.objects) + 1
                name = f"_anon_{number}"
                while name in rt.objects or name in env.values:
                    number += 1
                    name = f"_anon_{number}"
            else:
                name = await ev(a[1])
            try:
                env.get(name)
            except (KeyError, TypeError):
                pass
            else:
                raise KitleanError("Nazwa zajęta przez zmienną lub funkcję", n.line)
            rt.create(a[0], name)
            return name
        elif n.kind == "create_named":
            name = await self.statement(type(n)("create", n.line, (a[0], a[1])), env)
            prop = (
                "title"
                if a[0] == "gui.menu"
                else "file"
                if a[0] in ("item.sprite", "item.image", "audio.music")
                else "text"
            )
            await self.set_property(name, prop, a[2], env)
            return name
        elif n.kind == "action":
            arguments = []
            for expression in a[2]:
                if a[1] == "animate" and isinstance(expression, ast.Name):
                    arguments.append(expression.id)
                else:
                    arguments.append(await self.evaluate(expression, env, n.line))
            return rt.world.action(a[0], a[1], arguments)
        elif n.kind == "movement":
            entity = rt.get(a[0])
            if entity.kind != "item.sprite":
                raise KitleanError("Movement controls require a sprite", n.line)
            rt.set(entity.name, "speed", await ev(a[2]))
            rt.set(entity.name, "setting.move", a[1])
        elif n.kind == "copy":
            return rt.world.copy(a[0]).name
        elif n.kind == "delete":
            rt.remove(a[0])
        elif n.kind == "next_segment":
            return rt.world.next_segment(a[0])
        elif n.kind == "release_segment":
            name = rt.get(a[0]).name
            if name not in rt.world.maps:
                raise KitleanError("No segment transition before del last=copy", n.line)
            return rt.world.maps[name].release_previous()
        elif n.kind == "summon":
            target = await ev(a[2]) if a[2] is not None else None
            alias = await ev(a[3]) if a[3] is not None else None
            if alias is not None:
                try:
                    env.get(alias)
                except (KeyError, TypeError):
                    pass
                else:
                    raise KitleanError("NPC alias conflicts with a variable", n.line)
            return rt.world.summon(a[0], a[1], target, alias).name
        elif n.kind == "forever":

            async def repeat_frames():
                while not rt.closed:
                    await self.block(n.body, env)
                    if not rt.closed:
                        await Delay(1 / 60)

            rt.scheduler.submit(repeat_frames())
        elif n.kind == "create_text":
            await self.statement(type(n)("create", n.line, (a[0], None)), env)
            name = rt.last[(rt.context, a[0])]
            await self.set_property(name, "text", a[1], env)
        elif n.kind == "property":
            await self.set_property(a[0], a[1], a[2], env)
        elif n.kind == "last_text":
            name = rt.last.get((rt.context, a[0]))
            if name is None:
                raise KitleanError(
                    "Brak ostatniego elementu w bieżącym kontekście", n.line
                )
            await self.set_property(name, "text", a[1], env)
        elif n.kind == "assign":
            if (
                a[0] in rt.objects
                or a[0] in ("true", "false", "null")
                or a[0] in self.builtins
            ):
                raise KitleanError("Nazwa zastrzeżona lub zajęta", n.line)
            value = await ev(a[1])
            owner = env
            if not a[2]:
                try:
                    owner = env.resolve(a[0])
                except KeyError:
                    pass
            owner.values[a[0]] = value
            rt.variable_changed(owner, a[0])
        elif n.kind == "augment":
            try:
                owner = env.resolve(a[0])
            except KeyError:
                raise KitleanError("Nieznana zmienna: " + a[0], n.line) from None
            left = owner.get(a[0])
            right = await ev(a[2])
            if type(left) not in (int, float) or type(right) not in (int, float):
                raise KitleanMathError("Operator skrócony wymaga liczb", n.line)
            owner.values[a[0]] = {
                "+=": operator.add,
                "-=": operator.sub,
                "*=": operator.mul,
                ":=": operator.truediv,
            }[a[1]](left, right)
            rt.variable_changed(owner, a[0])
        elif n.kind in ("save", "load"):
            try:
                owner = env.resolve(a[0])
            except KeyError:
                raise KitleanError("Nieznana zmienna: " + a[0], n.line) from None
            if n.kind == "save":
                rt.storage.save(a[0], owner.get(a[0]), n.line)
            else:
                owner.values[a[0]] = rt.storage.load(a[0], owner.get(a[0]), n.line)
                rt.variable_changed(owner, a[0])
        elif n.kind in ("play", "pause", "resume", "stop", "start"):
            element = rt.get(a[0])
            if element.kind == "timer" and n.kind in ("start", "stop"):
                (rt.start_timer if n.kind == "start" else rt.stop_timer)(element)
            elif element.kind == "audio.music" and n.kind in (
                "play",
                "pause",
                "resume",
                "stop",
            ):
                rt.audio.command(
                    n.kind, element, rt.asset_path(element.properties["file"]), n.line
                )
            else:
                raise KitleanError("Niepoprawny typ obiektu dla " + n.kind, n.line)
        elif n.kind == "wait":
            seconds = rt.scheduler.seconds(await ev(a[0]), n.line)
            await Delay(seconds)
        elif n.kind == "key_event":
            if n.otherwise:
                raise KitleanError("Zdarzenia nie obsługują else", n.line)
            key = rt.keyboard.canonical(a[0], n.line)
            rt.events.register(
                "key",
                key,
                lambda: rt.scheduler.submit(self.block(n.body, env)),
                key=(id(n), id(env)),
            )
        elif n.kind == "function":
            if (
                a[0] in rt.objects
                or a[0] in self.builtins
                or a[0] in ("true", "false", "null")
            ):
                raise KitleanError("Nazwa zastrzeżona lub zajęta", n.line)
            env.values[a[0]] = Function(a[1], n.body, env)
        elif n.kind == "expression":
            await ev(a[0])
        elif n.kind == "repeat":
            count = await ev(a[0])
            if type(count) is not int or count < 0:
                raise KitleanError("repeat wymaga nieujemnej liczby całkowitej", n.line)
            for _ in range(count):
                await self.block(n.body, env)
        elif n.kind in ("if", "when"):
            tree = a[0].tree
            path = self.attribute_path(tree)
            event = None
            if path and len(path) == 2 and path[1] in ("clicked", "hovered", "tick"):
                element = rt.get(path[0])
                if (
                    path[1] == "tick"
                    and element.kind != "timer"
                    or path[1] != "tick"
                    and not element.kind.startswith("item.")
                ):
                    raise KitleanError("Event is not supported by this object", n.line)
                event = (element.name, path[1])
            elif (
                path
                and len(path) == 3
                and path[0] == "mouse"
                and path[1] in ("left", "right")
                and path[2] == "clicked"
            ):
                event = ("mouse", path[1] + ".clicked")
            elif path and len(path) == 3 and path[1] == "collided":
                source = rt.get(path[0])
                target = rt.get(path[2])
                if source.kind != "item.sprite" or target.kind != "item.sprite":
                    raise KitleanError("Collision events require sprites", n.line)
                event = (source.name, "collided." + target.name)
            elif path and len(path) == 3 and path[1:] == ["animation", "finished"]:
                source = rt.get(path[0])
                if source.kind != "item.sprite":
                    raise KitleanError("Animation events require a sprite", n.line)
                event = (source.name, "animation.finished")
            if event:
                if n.otherwise:
                    raise KitleanError("Events do not support else", n.line)
                rt.events.register(
                    *event,
                    lambda: rt.scheduler.submit(self.block(n.body, env)),
                    key=(id(n), id(env)),
                )
            elif n.kind == "when":
                raise KitleanError("when requires a supported event", n.line)
            else:
                await self.block(n.body if await ev(a[0]) else n.otherwise, env)
        elif n.kind == "run":
            rt.windows.open(await ev(a[0]))
            rt.scheduler.want_loop = True
            await GuiWait()
        elif n.kind == "run_context":
            if rt.context is None:
                raise KitleanError("Najpierw utwórz menu", n.line)
            rt.windows.open(rt.context)
            rt.scheduler.want_loop = True
            await GuiWait()
        elif n.kind == "open":
            rt.windows.open(await ev(a[0]))
        elif n.kind == "close":
            rt.windows.hide(await ev(a[0]))
        elif n.kind == "close_app":
            rt.windows.close()

    async def set_property(self, name, prop, expression, env):
        if isinstance(expression.tree, Template) and prop in ("text", "title", "value"):
            self.runtime.bind_text(name, prop, expression.tree, env, expression.line)
        else:
            self.runtime.set(
                name, prop, await self.evaluate(expression.tree, env, expression.line)
            )

    async def evaluate(self, n, env, line):
        self.runtime.line = line

        async def ev(x):
            return await self.evaluate(x, env, line)

        if isinstance(n, MathCall):
            return calculate(n.name, [await ev(x) for x in n.args], line)
        if isinstance(n, Template):
            return self.runtime.render_template(n, env, line)
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
            values = [await ev(x) for x in n.elts]
            return tuple(values) if isinstance(n, ast.Tuple) else values
        if isinstance(n, ast.Attribute):
            path = self.attribute_path(n)
            if path and len(path) == 4 and path[1:3] == ["outof", "gui"]:
                return self.runtime.world.outof(path[0], path[3])
            if not path:
                raise KitleanError("Unsupported attribute access", line)
            return self.runtime.read(path[0], ".".join(path[1:]))
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
            return ops[type(n.op)](await ev(n.left), await ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return {
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
                ast.Not: operator.not_,
            }[type(n.op)](await ev(n.operand))
        if isinstance(n, ast.BoolOp):
            value = await ev(n.values[0])
            for item in n.values[1:]:
                if (
                    isinstance(n.op, ast.And)
                    and not value
                    or isinstance(n.op, ast.Or)
                    and value
                ):
                    return value
                value = await ev(item)
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
            left = await ev(n.left)
            for op, right in zip(n.ops, n.comparators, strict=True):
                right = await ev(right)
                if not ops[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(n, ast.Subscript):
            return (await ev(n.value))[await ev(n.slice)]
        if isinstance(n, ast.Call):
            args = [await ev(x) for x in n.args]
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
            function = await ev(n.func)
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
                await self.block(function.body, local)
            finally:
                self.depth -= 1
            return None
        raise KitleanError("Niedozwolone wyrażenie", line)

    @staticmethod
    def attribute_path(node):
        names = []
        while isinstance(node, ast.Attribute):
            names.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        return [node.id] + list(reversed(names))
