"""A small stdlib-only tokenizer for syntax-highlighting fenced code blocks.

Not a real grammar-aware highlighter: regex-based token classification
(keyword/string/comment/number) for a handful of common languages, kept
dependency-free per md-ssg's zero-runtime-dependency principle. Unrecognized
languages fall back to plain (unhighlighted) rendering in markdown.py.
"""
import html
import re


def _kw(words):
    return r"\b(?:" + "|".join(sorted(words, key=len, reverse=True)) + r")\b"


_PY_KEYWORDS = _kw([
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
])

_JS_KEYWORDS = _kw([
    "await", "break", "case", "catch", "class", "const", "continue",
    "debugger", "default", "delete", "do", "else", "export", "extends",
    "false", "finally", "for", "function", "if", "import", "in",
    "instanceof", "let", "new", "null", "return", "super", "switch",
    "this", "throw", "true", "try", "typeof", "undefined", "var", "void",
    "while", "with", "yield",
])

_SHELL_KEYWORDS = _kw([
    "case", "do", "done", "elif", "else", "esac", "export", "fi", "for",
    "function", "if", "in", "local", "return", "then", "until", "while",
])

_LANG_SPECS = {
    "python": [
        ("comment", r"#[^\n]*"),
        ("string", r"(?:\"\"\".*?\"\"\"|'''.*?'''|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"),
        ("number", r"\b\d+(?:\.\d+)?\b"),
        ("keyword", _PY_KEYWORDS),
    ],
    "javascript": [
        ("comment", r"//[^\n]*|/\*.*?\*/"),
        ("string", r"(?:`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"),
        ("number", r"\b\d+(?:\.\d+)?\b"),
        ("keyword", _JS_KEYWORDS),
    ],
    "bash": [
        ("comment", r"#[^\n]*"),
        ("string", r"(?:\"(?:\\.|[^\"\\])*\"|'[^'\n]*')"),
        ("variable", r"\$\{?\w+\}?"),
        ("keyword", _SHELL_KEYWORDS),
    ],
    "json": [
        ("string", r"\"(?:\\.|[^\"\\])*\""),
        ("number", r"-?\b\d+(?:\.\d+)?\b"),
        ("keyword", r"\b(?:true|false|null)\b"),
    ],
}

_ALIASES = {
    "py": "python",
    "js": "javascript",
    "sh": "bash",
    "shell": "bash",
}


def supported_languages():
    """Every language name/alias `highlight` recognizes."""
    return sorted(set(_LANG_SPECS) | set(_ALIASES))


def highlight(code, lang):
    """Return HTML with `<span class="tok-*">`-wrapped tokens, or None if
    `lang` isn't a recognized language (caller should fall back to plain
    escaped rendering in that case)."""
    lang = (lang or "").strip().lower()
    lang = _ALIASES.get(lang, lang)
    spec = _LANG_SPECS.get(lang)
    if spec is None:
        return None

    pattern = re.compile(
        "|".join(f"(?P<{name}>{pat})" for name, pat in spec),
        re.DOTALL,
    )
    out = []
    pos = 0
    for m in pattern.finditer(code):
        if m.start() > pos:
            out.append(html.escape(code[pos:m.start()]))
        out.append(f'<span class="tok-{m.lastgroup}">{html.escape(m.group())}</span>')
        pos = m.end()
    out.append(html.escape(code[pos:]))
    return "".join(out)
