import io
import token
import tokenize
from dataclasses import dataclass

from .errors import KitleanError


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int


class Lexer:
    def __init__(self, source):
        self.source = source

    def tokenize(self):
        try:
            return [
                Token(token.tok_name[t.type], t.string, t.start[0], t.start[1])
                for t in tokenize.generate_tokens(io.StringIO(self.source).readline)
                if t.type not in (tokenize.COMMENT, tokenize.NL)
            ]
        except (tokenize.TokenError, IndentationError, SyntaxError) as e:
            line = getattr(e, "lineno", None) or (
                e.args[1][0] if len(e.args) > 1 and isinstance(e.args[1], tuple) else 1
            )
            raise KitleanError("Niepoprawna składnia lub wcięcia", line) from None
