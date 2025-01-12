import re


def escape_markdown_v2(text):
    """
    Escapes special characters for Telegram MarkdownV2.
    """
    escape_chars = r"*_[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def latex_to_markdown_v2(latex_content):
    # Replace LaTeX section and subsection headers with Markdown headers
    latex_content = re.sub(r'\\subsection\*{(.*?)}', r'\n **\1**', latex_content)

    # Replace LaTeX itemize lists with Markdown bullet lists
    latex_content = re.sub(r'\\begin{itemize}', '', latex_content)
    latex_content = re.sub(r'\\end{itemize}', '', latex_content)
    latex_content = re.sub(r'\\item (.*?)\\', r'* \1', latex_content)

    # Replace \texttt{} with Markdown's inline code formatting
    latex_content = re.sub(r'\\texttt{(.*?)}', r'`\1`', latex_content)
    latex_content = re.sub(r'texttt{(.*?)}', r'`\1`', latex_content)

    # Replace LaTeX verbatim with backticks for inline code
    latex_content = re.sub(r'\\verb\|(.*?)\|', r'`\1`', latex_content)

    # Replace LaTeX environments like \begin{example} ... \end{example} with Markdown code block formatting
    latex_content = re.sub(r'\\begin{example}', '```', latex_content)
    latex_content = re.sub(r'\\end{example}', '```', latex_content)

    # Clean up any remaining LaTeX commands
    latex_content = latex_content.replace("\\\\", "\n")  # LaTeX line breaks

    # Finally escape MarkdownV2 special characters after all conversions
    return escape_markdown_v2(latex_content)


# Example LaTeX content
exercise_data = {
    "title": "Mayor de dos números",
    "content": r"""
        Lee dos números enteros y muestra cuál de ellos es mayor, o indica si son iguales.
        \subsection*{Ejemplos}
        \begin{itemize}
            \item Entrada: \texttt{12, 7}\\
                Salida: \texttt{El número mayor es 12.}
            \item Entrada: \texttt{4, 9}\\
                Salida: \texttt{El número mayor es 9.}
            \item Entrada: \texttt{10, 10}\\
                Salida: \texttt{Ambos números son iguales.}
        \end{itemize}
    """,
    "difficulty": "Medium"
}

# Convert LaTeX content to MarkdownV2
markdown_content = latex_to_markdown_v2(exercise_data['content'])

# Display the output
print(markdown_content)
