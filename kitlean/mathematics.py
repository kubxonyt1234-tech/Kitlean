import math
import random

from .errors import KitleanMathError


def calculate(name, args, line):
    counts = {
        "random": 2,
        "round": 1,
        "sqrt": 1,
        "abs": 1,
        "min": 2,
        "max": 2,
        "pow": 2,
        "nww": 2,
        "nwd": 2,
    }
    if name not in counts or len(args) != counts[name]:
        raise KitleanMathError(
            "Nieznana funkcja lub liczba argumentów math/" + name, line
        )
    if any(
        type(x) not in (int, float) or (type(x) is float and not math.isfinite(x))
        for x in args
    ):
        raise KitleanMathError("Argumenty muszą być skończonymi liczbami", line)
    if name in ("random", "nww", "nwd") and any(type(x) is not int for x in args):
        raise KitleanMathError("Ta funkcja wymaga liczb całkowitych", line)
    functions = {
        "random": random.randint,
        "round": round,
        "sqrt": math.sqrt,
        "abs": abs,
        "min": min,
        "max": max,
        "pow": pow,
        "nww": math.lcm,
        "nwd": math.gcd,
    }
    try:
        value = functions[name](*args)
        if (
            isinstance(value, complex)
            or isinstance(value, float)
            and not math.isfinite(value)
        ):
            raise ValueError("wynik poza zakresem liczb rzeczywistych")
        return value
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        raise KitleanMathError(
            "Nieprawidłowy zakres math/" + name + ": " + str(e), line
        ) from None
