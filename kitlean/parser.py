import ast
import re
import token
import tokenize

from .ast_nodes import Expression, Statement
from .errors import KitleanError
from .lexer import Lexer

IDENT = r"[^\W\d]\w*"


class Parser:
    def __init__(self, source):
        self.tokens = Lexer(source).tokenize()
        self.pos = 0

    def expression(self, text, line):
        try:
            tree = ast.parse(text, mode="eval").body
        except SyntaxError:
            raise KitleanError("Niepoprawne wyrażenie: " + text, line) from None
        allowed = (
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

    def parse(self):
        return self.block(False)

    def block(self, nested):
        result = []
        while self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            if t.kind in ("NEWLINE",):
                self.pos += 1
                continue
            if t.kind == "ENDMARKER":
                break
            if t.kind == "DEDENT":
                if not nested:
                    raise KitleanError("Nieoczekiwane wcięcie", t.line)
                self.pos += 1
                return result
            if t.kind == "INDENT":
                raise KitleanError("Nieoczekiwane wcięcie", t.line)
            row = []
            while self.tokens[self.pos].kind not in ("NEWLINE", "ENDMARKER"):
                row.append(self.tokens[self.pos])
                self.pos += 1
            if self.tokens[self.pos].kind == "NEWLINE":
                self.pos += 1
            text = tokenize.untokenize(
                [
                    (
                        token.NAME
                        if x.kind == "NAME"
                        else token.STRING
                        if x.kind == "STRING"
                        else token.NUMBER
                        if x.kind == "NUMBER"
                        else token.OP,
                        x.value,
                    )
                    for x in row
                ]
            ).strip()
            compact = "".join(x.value for x in row)
            line = t.line

            def expr(s, row=row, line=line):
                # Odtwórz odstępy tokenów wyrażenia (np. true and false).
                for start in range(len(row)):
                    joined = ""
                    for end in range(start, len(row)):
                        joined += row[end].value
                        if joined == s:
                            pairs = [
                                (
                                    token.NAME
                                    if x.kind == "NAME"
                                    else token.STRING
                                    if x.kind == "STRING"
                                    else token.NUMBER
                                    if x.kind == "NUMBER"
                                    else token.OP,
                                    x.value,
                                )
                                for x in row[start : end + 1]
                            ]
                            return self.expression(tokenize.untokenize(pairs), line)
                        if len(joined) > len(s):
                            break
                return self.expression(s, line)

            node = None
            m = re.fullmatch(
                r"\[create(gui\.menu|item\.(?:button|input|label|checkbox))=(.+)\]",
                compact,
            )
            if m:
                node = Statement("create", line, (m[1], expr(m[2])))
            m = re.fullmatch(
                r"create(item\.(?:button|input|label|checkbox))/(.+)", compact
            )
            if m:
                node = Statement("last_text", line, (m[1], expr(m[2])))
            m = re.fullmatch(rf"({IDENT})\.({IDENT})/(.+)", compact)
            if m and node is None:
                node = Statement("property", line, (m[1], m[2], expr(m[3])))
            m = re.fullmatch(r"rungui\.menu=(.+)", compact)
            if m:
                node = Statement("run", line, (expr(m[1]),))
            if compact == "close.app":
                node = Statement("close_app", line)
            m = re.fullmatch(rf"var\s+({IDENT})\s*=\s*(.+)", text)
            if not m:
                m = re.fullmatch(rf"({IDENT})\s*=\s*(.+)", text)
            if m:
                node = Statement("assign", line, (m[1], expr(m[2])))
            header = None
            if row[0].value in ("if", "repeat", "function", "else"):
                if row[-1].value != ":":
                    raise KitleanError("Oczekiwano ':'", line)
                header = row[0].value
                content = tokenize.untokenize(
                    [
                        (
                            token.NAME
                            if x.kind == "NAME"
                            else token.STRING
                            if x.kind == "STRING"
                            else token.NUMBER
                            if x.kind == "NUMBER"
                            else token.OP,
                            x.value,
                        )
                        for x in row[1:-1]
                    ]
                ).strip()
                if header == "else":
                    if (
                        content
                        or not result
                        or result[-1].kind != "if"
                        or result[-1].otherwise
                    ):
                        raise KitleanError("Nieoczekiwane else", line)
                elif header == "function":
                    fm = re.fullmatch(rf"({IDENT})\s*\((.*?)\)", content)
                    if not fm:
                        raise KitleanError("Niepoprawna deklaracja funkcji", line)
                    params = (
                        [p.strip() for p in fm[2].split(",")] if fm[2].strip() else []
                    )
                    if len(set(params)) != len(params) or any(
                        not re.fullmatch(IDENT, p) for p in params
                    ):
                        raise KitleanError("Niepoprawne parametry", line)
                    node = Statement("function", line, (fm[1], params))
                else:
                    node = Statement(header, line, (expr(content),))
                if (
                    self.pos >= len(self.tokens)
                    or self.tokens[self.pos].kind != "INDENT"
                ):
                    raise KitleanError("Oczekiwano wciętego bloku", line)
                self.pos += 1
                body = self.block(True)
                if header == "else":
                    result[-1].otherwise = body
                    continue
                node.body = body
            if node is None:
                node = Statement("expression", line, (expr(text),))
            result.append(node)
        return result
