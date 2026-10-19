import ast
import re
import token
import tokenize

from .ast_nodes import Expression, Statement, Template
from .errors import KitleanError
from .lexer import Lexer

IDENT = r"[^\W\d]\w*"
KINDS = {"gui": {"menu"}, "item": {"button", "label", "input", "checkbox"}}
TEXT_PROPERTIES = {"text", "title", "background", "color", "parent"}


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
        text = source_text(tokens)
        try:
            tree = ast.parse(text, mode="eval").body
        except SyntaxError:
            raise KitleanError("Niepoprawne wyrażenie: " + text, line) from None
        templates = self.templates

        class ConvertTemplates(ast.NodeTransformer):
            def visit_Name(self, node):
                return templates.get(node.id, node)

        tree = ConvertTemplates().visit(tree)
        allowed = (
            Template,
            ast.Constant,
            ast.Name,
            ast.Load,
            ast.List,
            ast.Tuple,
            ast.BinOp,
            ast.UnaryOp,
            ast.BoolOp,
            ast.Compare,
            ast.Call,
            ast.Attribute,
            ast.Subscript,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.UAdd,
            ast.Not,
            ast.And,
            ast.Or,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.In,
            ast.NotIn,
        )
        if any(not isinstance(n, allowed) for n in ast.walk(tree)):
            raise KitleanError("Niedozwolone wyrażenie", line)
        return Expression(tree, line)

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
            if head in ("if", "repeat", "function", "else"):
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
                    node = Statement(head, line, (self.expression(row[1:-1], line),))
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
            nodes.append(self.simple(row, line))
        return nodes

    def simple(self, row, line):
        v = [t.value for t in row]
        head = v[0]
        if head == "[" or head == "create":
            bracket = head == "["
            tokens = row[1:-1] if bracket else row
            if bracket and v[-1] != "]":
                raise KitleanError("Brak zamknięcia ]", line)
            vals = [t.value for t in tokens]
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
