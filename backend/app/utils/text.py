import re
from bs4 import BeautifulSoup

_STRIP_TAGS = [
    "script", "style", "nav", "footer", "header",
    "form", "button", "input", "select", "option",
    "img", "svg", "iframe", "noscript", "aside",
]


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    # Prefer semantic content blocks when present
    main = (
        soup.find(["main", "article"])
        or soup.find(id=re.compile(r"about|content|main", re.I))
    )
    target = main or soup.body or soup

    lines = []
    for line in target.get_text(separator="\n").splitlines():
        line = line.strip()
        if len(line) >= 30:  # drop nav links, button labels, lone words
            lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"
