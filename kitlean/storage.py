import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

from .errors import KitleanError


class Storage:
    def __init__(self, program, data_root=None):
        identity = str(Path(program).resolve()).casefold()
        root = (
            Path(data_root)
            if data_root
            else Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share"))
            / "Kitlean"
            / "saves"
        )
        self.path = (
            root / hashlib.sha256(identity.encode()).hexdigest() / "variables.json"
        )

    def valid(self, value):
        if type(value) in (str, bool, int, type(None)):
            return True
        if type(value) is float:
            return math.isfinite(value)
        return type(value) is list and all(self.valid(x) for x in value)

    def read(self, line):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if type(data) is not dict or any(
                not isinstance(k, str) or not self.valid(v) for k, v in data.items()
            ):
                raise ValueError("niepoprawne typy")
            return data
        except (OSError, ValueError, RecursionError) as e:
            raise KitleanError(
                "Nie można wczytać zapisu JSON: " + str(e), line
            ) from None

    def load(self, name, default, line):
        return self.read(line).get(name, default)

    def save(self, name, value, line):
        if not self.valid(value):
            raise KitleanError(
                "save obsługuje liczby, tekst, boolean, null i listy", line
            )
        temporary = None
        try:
            data = self.read(line)
            data[name] = value
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as f:
                temporary = Path(f.name)
                json.dump(data, f, ensure_ascii=False, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, self.path)
        except (OSError, ValueError) as e:
            raise KitleanError("Nie można zapisać danych: " + str(e), line) from None
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
