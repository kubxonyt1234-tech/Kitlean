class KitleanError(Exception):
    def __init__(self, message, line=1, hint=None):
        self.message, self.line, self.hint = message, line, hint
        super().__init__(message)

    def __str__(self):
        return f"KitleanError [Line {self.line}]\n{self.message}" + (
            f"\n\nHint: {self.hint}" if self.hint else ""
        )
