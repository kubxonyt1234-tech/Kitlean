import argparse
import sys
from pathlib import Path

from .errors import KitleanError
from .interpreter import Interpreter
from .parser import Parser


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="kitlean",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Kitlean 0.2 Beta — interpreter języka i GUI tkinter",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Kitlean 0.2 Beta\nPython-powered programming language",
    )
    sub = parser.add_subparsers(dest="command")
    for cmd in ("run", "check"):
        sub.add_parser(cmd).add_argument("file", type=Path)
    sub.add_parser("help")
    args = parser.parse_args(argv)
    if args.command in (None, "help"):
        parser.print_help()
        return 0
    interpreter = None
    try:
        source = args.file.read_text(encoding="utf-8-sig")
        if args.command == "check":
            Parser(source).parse()
            print("Składnia poprawna: " + str(args.file))
        else:
            interpreter = Interpreter()
            interpreter.execute(source)
        return 0
    except KitleanError as e:
        print(e, file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as e:
        print(KitleanError("Nie można odczytać pliku: " + str(e)), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Przerwano.", file=sys.stderr)
        return 130
    finally:
        if interpreter:
            interpreter.runtime.windows.close()
