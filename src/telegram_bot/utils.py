from typing import Callable

from telegram.helpers import escape_markdown

from database.database import SessionLocal


def inject_services(cls):
    """ Class decorator that initializes services before executing any method """

    def ensure_services_before_call(method: Callable):
        """ Wrapper to initialize services before each method call """

        def wrapper(self, *args, **kwargs):
            with SessionLocal() as session:
                self._initialize_services(session)  # Initialize services on each method call
                return method(self, *args, **kwargs)

        return wrapper

    # Automatically decorate all methods, except dunder methods (__init__, __str__, etc.)
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value) and not attr_name.startswith("_"):
            setattr(cls, attr_name, ensure_services_before_call(attr_value))

    return cls


def format_solution(solution: str) -> str:
    parts = solution.split("```")
    formatted_parts = []

    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Es texto, escapa los caracteres especiales de MarkdownV2
            formatted_parts.append(escape_markdown(part, version=2))
        else:
            # Es código, envuélvelo en un bloque de código
            formatted_parts.append(f"```{part}```")

    return "".join(formatted_parts)
