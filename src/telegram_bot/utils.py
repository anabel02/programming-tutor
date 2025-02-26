from telegram.helpers import escape_markdown


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
