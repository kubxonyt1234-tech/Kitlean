import io
import re
import token
import tokenize
from dataclasses import dataclass

from .ast_nodes import Template
from .errors import KitleanError


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int


class Lexer:
    """Skanuje literały Kitlean, następnie tokeny wyrażeń i wcięcia."""

    def __init__(self, source):
        self.source = source
        self.templates = {}

    def scan_template(self, start, line, path_mode=False):
        parts, literal = [], []
        i = start + 1
        escapes = {
            "$": "$",
            "{": "{",
            "}": "}",
            "\\": "\\",
            "n": "\n",
            "t": "\t",
            "r": "\r",
        }
        while i < len(self.source):
            ch = self.source[i]
            if ch in "\r\n":
                break
            if ch == "\\":
                i += 1
                if (
                    path_mode
                    and i < len(self.source)
                    and self.source[i] not in ("$", "{", "}", "\\")
                ):
                    literal.extend(("\\", self.source[i]))
                    i += 1
                    continue
                if i >= len(self.source) or self.source[i] not in escapes:
                    raise KitleanError("Niepoprawna sekwencja ucieczki w tekście", line)
                literal.append(escapes[self.source[i]])
            elif ch == "$":
                parts.append((False, "".join(literal)))
                return Template(parts, line), i + 1
            elif ch == "{":
                end = self.source.find("}", i + 1)
                if end < 0 or "\n" in self.source[i:end]:
                    raise KitleanError("Brak zamknięcia interpolacji }", line)
                name = self.source[i + 1 : end]
                if not name.isidentifier():
                    raise KitleanError(
                        "Interpolacja wymaga nazwy zmiennej: {nazwa}", line
                    )
                parts.append((False, "".join(literal)))
                literal = []
                parts.append((True, name))
                i = end
            elif ch == "}":
                raise KitleanError("Dosłowny nawias } zapisz jako \\}", line)
            else:
                literal.append(ch)
            i += 1
        raise KitleanError(
            "Brak zamykającego znaku $", line, "Zamknij tekst znakiem $."
        )

    def prepare(self):
        # Skaner literałów; cytowane stringi i komentarze zachowują znaczenie.
        output, i, line = [], 0, 1
        quote = re.compile(
            r"(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\")"
        )
        while i < len(self.source):
            ch = self.source[i]
            if self.source.startswith("__kitlean_template_", i):
                raise KitleanError("Nazwa zastrzeżona dla interpretera", line)
            if ch in "'\"":
                match = quote.match(self.source, i)
                if match:
                    text = match[0]
                    output.append(text)
                    line += text.count("\n")
                    i = match.end()
                    continue
            if ch == "#":
                end = self.source.find("\n", i)
                end = len(self.source) if end < 0 else end
                output.append(self.source[i:end])
                i = end
                continue
            if ch == "$":
                prefix = self.source[self.source.rfind("\n", 0, i) + 1 : i]
                template, end = self.scan_template(
                    i, line, bool(re.search(r"\.\s*file\s*/\s*$", prefix))
                )
                name = f"__kitlean_template_{len(self.templates)}"
                self.templates[name] = template
                output.append(name)
                i = end
                continue
            output.append(ch)
            line += ch == "\n"
            i += 1
        return "".join(output)

    def tokenize(self):
        source = self.prepare()
        try:
            return [
                Token(token.tok_name[t.type], t.string, t.start[0], t.start[1])
                for t in tokenize.generate_tokens(io.StringIO(source).readline)
                if t.type not in (tokenize.COMMENT, tokenize.NL)
            ]
        except (tokenize.TokenError, IndentationError, SyntaxError) as e:
            line = getattr(e, "lineno", None) or (
                e.args[1][0] if len(e.args) > 1 and isinstance(e.args[1], tuple) else 1
            )
            raise KitleanError("Niepoprawna składnia lub wcięcia", line) from None
