import re


def escape_markdown_v2(text):
    """
    Escapes special characters for Telegram MarkdownV2.
    """
    escape_chars = r"*_[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def latex_to_markdown_v2(latex_content):
    """
    Converts LaTeX content into MarkdownV2-compatible text for Telegram, 
    including handling LaTeX formulas and text formatting.
    """
    # Remove \textcolor{color}{...} commands
    latex_content = re.sub(r'\\textcolor\{.*?\}\{(.*?)\}', r'\1', latex_content)

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

    # Handle LaTeX math mode for inline and display formulas
    # Inline formulas ($...$) should be wrapped with MarkdownV2 inline preformat
    latex_content = re.sub(r'\$(.*?)\$', r'`\1`', latex_content)

    # Display formulas (\[...\] or $$...$$) should be wrapped with MarkdownV2 code block
    latex_content = re.sub(r'\\\[(.*?)\\\]', r'```\1```', latex_content)
    latex_content = re.sub(r'\$\$(.*?)\$\$', r'```\1```', latex_content)

    # Replace LaTeX environments like \begin{example} ... \end{example} with Markdown code block formatting
    latex_content = re.sub(r'\\begin{example}', '```', latex_content)
    latex_content = re.sub(r'\\end{example}', '```', latex_content)

    # Handle LaTeX commands like \textit{} for italic
    latex_content = re.sub(r'\\textit{(.*?)}', r'*\1*', latex_content)

    # Replace common LaTeX special characters with Markdown-safe equivalents
    # latex_content = latex_content.replace("\\\\", "\n")  # LaTeX line breaks

    # Escape MarkdownV2 special characters
    return escape_markdown_v2(latex_content)


# Example LaTeX content
exercise_data = {
    "title": "Mayor de dos números",
    "content": r"""
   Escribe un programa que determine si un entero es primo o no.

    Un número entero positivo \( n \) se dice que es \textit{primo} si tiene exactamente dos divisores distintos: \( 1 \) y el propio número \( n \). Es decir, \( n \) es primo si y solo si no existen otros divisores \( d \) tal que \( 1 < d < n \) y \( d \) divide a \( n \). Formalmente, podemos escribir:
    \[
    n \text{ es primo} \iff  \forall d \in \mathbb{Z}^+ \, \text{se cumple que si} \, d \mid n \text{, entonces } d = 1 \text{ o } d = n.
    \]

    Donde \( \mathbb{Z}^+ \) representa el conjunto de los números enteros positivos, y \( d \mid n \) denota que \( d \) divide a \( n \), es decir, \( n \) es divisible por \( d \).
    \subsection*{Ejemplos}
    \begin{itemize}
        \item Entrada: \texttt{10}\\
            Salida: \textcolor{blue}{false}
        \item Entrada: \texttt{29}\\
            Salida: \textcolor{blue}{true}
        \item Entrada: \texttt{15}\\
            Salida: \textcolor{blue}{false}
        \item Entrada: \texttt{31}\\
            Salida: \textcolor{blue}{true}
    \end{itemize}
    """,
    "difficulty": "Medium"
}

# Convert LaTeX content to MarkdownV2
markdown_content = latex_to_markdown_v2(exercise_data['content'])

# # Display the output
# print(markdown_content)
