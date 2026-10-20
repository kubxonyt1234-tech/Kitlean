import ast
import re
import token
import tokenize

from .ast_nodes import Expression, Statement
from .errors import KitleanError
from .expressions import Expressions
from .lexer import Lexer

IDENT = r"[^\W\d]\w*"
KINDS = {
    "gui": {"menu"},
    "item": {"button", "label", "input", "checkbox", "image", "sprite"},
    "audio": {"music"},
}
TEXT_PROPERTIES = {"text", "title", "background", "color", "parent", "file"}


def source_text(tokens):
    return tokenize.untokenize(
        [(getattr(token, t.kind, token.OP), t.value) for t in tokens]
    ).strip()


class Parser:
    def __init__(self, source):
        lexer = Lexer(source)
        self.tokens = lexer.tokenize()
        self.templates = lexer.templates
        self.pos = 0

    def expression(self, tokens, line):
        return Expressions(tokens, self.templates, line).parse()

    def value(self, tokens, line, text=False):
        if not tokens:
            raise KitleanError("Brak wartości po /", line)
        if not text:
            return self.expression(tokens, line)
        if (
            tokens[0].kind == "STRING"
            or tokens[0].value in self.templates
            or len(tokens) > 1
            and tokens[0].kind == "NAME"
            and tokens[1].value == "("
        ):
            return self.expression(tokens, line)
        # Wartość tekstowa bez delimitera jest pojedynczym ciągiem bez spacji.
        for a, b in zip(tokens, tokens[1:], strict=False):
            if a.line != b.line or b.column > a.column + len(a.value):
                raise KitleanError(
                    "Invalid text value.", line, "Use $...$ for text containing spaces."
                )
        return Expression(ast.Constant("".join(t.value for t in tokens)), line)

    def parse(self):
        return self.block(False)

    def block(self, nested):
        nodes = []
        while self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            if t.kind == "NEWLINE":
                self.pos += 1
                continue
            if t.kind == "ENDMARKER":
                return nodes
            if t.kind == "DEDENT":
                if not nested:
                    raise KitleanError("Nieoczekiwane wcięcie", t.line)
                self.pos += 1
                return nodes
            if t.kind == "INDENT":
                raise KitleanError("Nieoczekiwane wcięcie", t.line)
            row = []
            while self.tokens[self.pos].kind not in ("NEWLINE", "ENDMARKER"):
                row.append(self.tokens[self.pos])
                self.pos += 1
            if self.tokens[self.pos].kind == "NEWLINE":
                self.pos += 1
            line = t.line
            values = [x.value for x in row]
            head = values[0]
            if head in ("if", "when", "repeat", "function", "else"):
                if values[-1] != ":":
                    raise KitleanError("Oczekiwano ':'", line)
                if head == "else":
                    if (
                        len(row) != 2
                        or not nodes
                        or nodes[-1].kind != "if"
                        or nodes[-1].otherwise
                    ):
                        raise KitleanError("Nieoczekiwane else", line)
                    node = None
                elif head == "function":
                    content = source_text(row[1:-1])
                    match = re.fullmatch(rf"({IDENT})\s*\((.*?)\)", content)
                    if not match:
                        raise KitleanError("Niepoprawna deklaracja funkcji", line)
                    params = (
                        [x.strip() for x in match[2].split(",")]
                        if match[2].strip()
                        else []
                    )
                    if len(params) != len(set(params)) or any(
                        not re.fullmatch(IDENT, p) for p in params
                    ):
                        raise KitleanError("Niepoprawne parametry", line)
                    node = Statement("function", line, (match[1], params))
                else:
                    if head in ("if", "when") and values[1:3] in (
                        ["key", "/"],
                        ["key", "."],
                    ):
                        if len(row) == 7 and values[4:6] == [".", "pressed"]:
                            key_name = values[3]
                        elif (
                            len(row) == 6
                            and row[3].kind == "NUMBER"
                            and len(values[3]) == 2
                            and values[3][0].isdigit()
                            and values[3][1] == "."
                            and values[4] == "pressed"
                        ):
                            key_name = values[3][0]
                        else:
                            raise KitleanError("Użyj if key/SPACE.pressed:", line)
                        node = Statement("key_event", line, (key_name,))
                    elif head == "repeat" and values[1:-1] == ["forever"]:
                        node = Statement("forever", line)
                    else:
                        node = Statement(
                            head, line, (self.expression(row[1:-1], line),)
                        )
                if self.tokens[self.pos].kind != "INDENT":
                    raise KitleanError("Oczekiwano wciętego bloku", line)
                self.pos += 1
                body = self.block(True)
                if node is None:
                    nodes[-1].otherwise = body
                else:
                    node.body = body
                    nodes.append(node)
                continue
            node = self.simple(row, line)
            if node.kind == "thene" and (
                not nodes
                or nodes[-1].kind in ("if", "when", "key_event", "function", "forever")
            ):
                raise KitleanError(
                    "thene requires a previous executable instruction", line
                )
            nodes.append(node)
        return nodes

    def simple(self, row, line):
        v = [t.value for t in row]
        head = v[0]
        if head == "thene":
            if len(row) < 2:
                raise KitleanError("Missing instruction after thene", line)
            return Statement("thene", line, (self.simple(row[1:], line),))
        if head == "del":
            if len(v) == 6 and v[2:] == [".", "last", "=", "copy"]:
                return Statement("release_segment", line, (v[1],))
            if len(row) != 2 or row[1].kind != "NAME":
                raise KitleanError("Use del alias or del game.last=copy", line)
            return Statement("delete", line, (v[1],))
        if head == "summon" or head == "[" and len(v) > 1 and v[1] == "summon":
            return self.summon(row, line)
        if head == "create" and len(v) >= 4 and v[2] == ".":
            if len(v) == 6 and v[3:] == ["gui", ".", "next"]:
                return Statement("next_segment", line, (v[1],))
            if len(v) == 4 and v[3] == "copy":
                return Statement("copy", line, (v[1],))
        # Property chains and object actions are parsed before command keywords.
        if len(v) >= 3 and row[0].kind == "NAME" and v[1] == ".":
            cursor = 1
            names = []
            while (
                cursor + 1 < len(v)
                and v[cursor] == "."
                and row[cursor + 1].kind == "NAME"
            ):
                names.append(v[cursor + 1])
                cursor += 2
            if names and names[0] == "action":
                if len(names) != 2:
                    raise KitleanError("Use alias.action.name", line)
                if cursor == len(v):
                    return Statement("action", line, (v[0], names[1], []))
                expression = self.expression(row, line).tree
                if not isinstance(expression, ast.Call):
                    raise KitleanError("Invalid action arguments", line)
                return Statement("action", line, (v[0], names[1], expression.args))
            if cursor < len(v) and v[cursor] in ("=", "/"):
                prop = ".".join(names)
                tail = row[cursor + 1 :]
                if prop == "setting.move":
                    if (
                        len(tail) < 3
                        or tail[0].value not in ("wsad", "arrows")
                        or tail[1].value != "/"
                    ):
                        raise KitleanError(
                            "Use setting.move=wsad/speed or arrows/speed", line
                        )
                    return Statement(
                        "movement",
                        line,
                        (v[0], tail[0].value, self.expression(tail[2:], line)),
                    )
                if (
                    prop in ("align", "save", "camera.follow")
                    or prop == "position"
                    and len(tail) == 1
                    and tail[0].value == "random"
                ):
                    value = self.value(tail, line, text=True)
                else:
                    value = self.value(
                        tail, line, text=v[cursor] == "/" and prop in TEXT_PROPERTIES
                    )
                return Statement("property", line, (v[0], prop, value))
        if head == "[" or head == "create":
            bracket = head == "["
            tokens = row[1:-1] if bracket else row
            if bracket and v[-1] != "]":
                raise KitleanError("Brak zamknięcia ]", line)
            vals = [t.value for t in tokens]
            if len(vals) >= 2 and vals[:2] == ["create", "timer"]:
                tail = tokens[2:]
                if bracket:
                    if len(tail) < 2 or tail[0].value != "=":
                        raise KitleanError('Oczekiwano ="alias"', line)
                    return Statement(
                        "create", line, ("timer", self.expression(tail[1:], line))
                    )
                if tail:
                    raise KitleanError("Niepoprawne create timer", line)
                return Statement("create", line, ("timer", None))
            if (
                len(vals) < 4
                or vals[0] != "create"
                or vals[1] not in KINDS
                or vals[2] not in ("/", ".")
                or vals[3] not in KINDS[vals[1]]
            ):
                raise KitleanError(
                    "Niepoprawna składnia create: użyj create gui/menu lub create item/button",
                    line,
                )
            kind = vals[1] + "." + vals[3]
            tail = tokens[4:]
            if bracket and tail and tail[0].value == "/":
                expanded = []
                for token_item in tail:
                    if token_item.value == "!=":
                        expanded.extend(
                            (
                                type(token_item)(
                                    "OP", "!", token_item.line, token_item.column
                                ),
                                type(token_item)(
                                    "OP", "=", token_item.line, token_item.column + 1
                                ),
                            )
                        )
                    else:
                        expanded.append(token_item)
                tail = expanded
            if len(tail) > 1 and tail[0].value == "/":
                equals = next(
                    (i for i, t in enumerate(tail[1:], 1) if t.value == "="), None
                )
                if bracket:
                    if equals is None:
                        raise KitleanError('Aliased creation requires ="alias"', line)
                    return Statement(
                        "create_named",
                        line,
                        (
                            kind,
                            self.expression(tail[equals + 1 :], line),
                            self.value(tail[1:equals], line, text=True),
                        ),
                    )
                if (
                    kind == "gui.menu"
                    or vals[2] == "."
                    and tail[1].kind != "STRING"
                    or kind == "item.sprite"
                ):
                    return Statement(
                        "create_named",
                        line,
                        (kind, None, self.value(tail[1:], line, text=True)),
                    )
            if bracket:
                if len(tail) < 2 or tail[0].value != "=":
                    raise KitleanError('Oczekiwano ="alias"', line)
                return Statement(
                    "create", line, (kind, self.expression(tail[1:], line))
                )
            if not tail:
                return Statement("create", line, (kind, None))
            if tail[0].value != "/":
                raise KitleanError("Oczekiwano / przed tekstem", line)
            text = self.value(tail[1:], line, text=True)
            if vals[2] == ".":
                return Statement("last_text", line, (kind, text))
            return Statement("create_text", line, (kind, text))
        if v == ["close", ".", "app"]:
            return Statement("close_app", line)
        if head in ("play", "pause", "resume", "stop", "start", "save", "load") and (
            len(row) < 2 or v[1] not in (".", "(", "=")
        ):
            if len(row) != 2 or row[1].kind != "NAME":
                raise KitleanError("Oczekiwano nazwy po " + head, line)
            return Statement(head, line, (v[1],))
        if head == "wait" and len(row) > 1 and v[1] == "/":
            return Statement("wait", line, (self.expression(row[2:], line),))
        if len(row) > 2 and row[0].kind == "NAME" and v[1] in ("+=", "-=", "*=", ":="):
            return Statement(
                "augment", line, (v[0], v[1], self.expression(row[2:], line))
            )
        if head in ("run", "open", "close"):
            if len(row) == 2 and row[1].kind == "NAME":
                return Statement(head, line, (Expression(ast.Constant(v[1]), line),))
            if head == "run" and len(row) == 1:
                return Statement("run_context", line)
            if head == "run" and v[1:5] == ["gui", ".", "menu", "="]:
                return Statement("run", line, (self.expression(row[5:], line),))
            # Stare wywołania open.gui.menu(...), close.gui.menu(...).
            if len(row) > 1 and v[1] == ".":
                return Statement("expression", line, (self.expression(row, line),))
            raise KitleanError("Oczekiwano aliasu menu", line)
        declared = head == "var"
        offset = 2 if declared and len(v) > 1 and v[1] == "/" else 1 if declared else 0
        if (
            len(row) > offset + 1
            and row[offset].kind == "NAME"
            and v[offset + 1] == "="
        ):
            return Statement(
                "assign",
                line,
                (v[offset], self.expression(row[offset + 2 :], line), declared),
            )
        if (
            len(row) >= 4
            and row[0].kind == "NAME"
            and v[1] == "."
            and row[2].kind == "NAME"
            and v[3] == "/"
        ):
            return Statement(
                "property",
                line,
                (v[0], v[2], self.value(row[4:], line, text=v[2] in TEXT_PROPERTIES)),
            )
        return Statement("expression", line, (self.expression(row, line),))

    def summon(self, row, line):
        bracket = row[0].value == "["
        tokens = row[1:-1] if bracket else row
        v = [t.value for t in tokens]
        if bracket and row[-1].value != "]":
            raise KitleanError("Missing ]", line)
        random_mode = v[1:4] == ["random", ".", "npc"]
        offset = 4 if random_mode else 2
        if (
            not random_mode
            and v[1:2] != ["npc"]
            or len(v) <= offset + 1
            or v[offset] != "/"
            or tokens[offset + 1].kind != "NAME"
        ):
            raise KitleanError(
                "Use summon npc/template=(x,y) or summon random.npc/template", line
            )
        template = v[offset + 1]
        tail = tokens[offset + 2 :]
        target = alias = None
        if tail:
            if tail[0].value != "=" or len(tail) < 2:
                raise KitleanError("Invalid summon parameters", line)
            if bracket:
                alias = self.expression(tail[1:], line)
            elif len(tail) == 2 and tail[1].kind == "NAME":
                target = Expression(ast.Constant(tail[1].value), line)
            else:
                target = self.expression(tail[1:], line)
        return Statement("summon", line, (template, random_mode, target, alias))
