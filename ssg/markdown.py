"""A small markdown-subset -> HTML renderer (headers, lists, code, emphasis,
links, paragraphs). Not CommonMark-complete, but enough for real prose."""
import html
import re

from .highlight import highlight as _highlight_code

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"\*([^*]+)\*")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_TABLE_SEPARATOR_CELL = re.compile(r"^:?-+:?$")
_LIST_ITEM = re.compile(r"^(\s*)[-*]\s+(.*)$")
_QUOTE_LINE = re.compile(r"^>\s?(.*)$")


def _split_table_row(line):
    """Split a `| a | b |`-style row into cells, tolerating missing outer pipes."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _table_alignments(separator_cells):
    aligns = []
    for cell in separator_cells:
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            aligns.append("center")
        elif right:
            aligns.append("right")
        elif left:
            aligns.append("left")
        else:
            aligns.append(None)
    return aligns


def _is_table_separator(line):
    cells = _split_table_row(line)
    return bool(cells) and all(_TABLE_SEPARATOR_CELL.match(c) for c in cells)


def _render_list(items):
    """Render a flat (indent, text) item list into a nested <ul> tree.

    A dedent walks back up one recursion level at a time, comparing
    against each level's own base indent, so a jump across multiple
    levels at once (malformed/inconsistent indentation) still resolves
    correctly instead of crashing or losing items.
    """

    def render_level(idx, base_indent):
        out = ["<ul>"]
        while idx < len(items) and items[idx][0] >= base_indent:
            indent, text = items[idx]
            li = f"<li>{_render_inline(text)}"
            idx += 1
            if idx < len(items) and items[idx][0] > indent:
                nested_html, idx = render_level(idx, items[idx][0])
                li += nested_html
            li += "</li>"
            out.append(li)
        out.append("</ul>")
        return "\n".join(out), idx

    html_str, _ = render_level(0, items[0][0])
    return html_str


def _render_inline(text):
    text = html.escape(text, quote=False)
    text = _INLINE_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _ITALIC.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    text = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    return text


def render(source):
    """Render a markdown-subset document to an HTML fragment."""
    lines = source.splitlines()
    out = []
    i = 0
    paragraph = []
    list_items = None
    quote_lines = None

    def flush_paragraph():
        if paragraph:
            out.append("<p>" + _render_inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def flush_list():
        nonlocal list_items
        if list_items is not None:
            out.append(_render_list(list_items))
            list_items = None

    def flush_quote():
        nonlocal quote_lines
        if quote_lines is not None:
            text = " ".join(quote_lines)
            out.append("<blockquote><p>" + _render_inline(text) + "</p></blockquote>")
            quote_lines = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_quote()
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code_text = "\n".join(code_lines)
            highlighted = _highlight_code(code_text, lang) if lang else None
            if highlighted is not None:
                out.append(
                    f'<pre><code class="language-{html.escape(lang)}">{highlighted}</code></pre>'
                )
            else:
                out.append(f"<pre><code>{html.escape(code_text)}</code></pre>")
            i += 1
            continue

        header_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if header_match:
            flush_paragraph()
            flush_list()
            flush_quote()
            level = len(header_match.group(1))
            out.append(f"<h{level}>{_render_inline(header_match.group(2))}</h{level}>")
            i += 1
            continue

        if (
            "|" in stripped
            and i + 1 < len(lines)
            and _is_table_separator(lines[i + 1].strip())
        ):
            flush_paragraph()
            flush_list()
            flush_quote()
            header_cells = _split_table_row(stripped)
            aligns = _table_alignments(_split_table_row(lines[i + 1].strip()))
            i += 2
            body_rows = []
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                body_rows.append(_split_table_row(lines[i]))
                i += 1

            def _style(idx):
                align = aligns[idx] if idx < len(aligns) else None
                return f' style="text-align: {align}"' if align else ""

            out.append("<table>")
            out.append("<thead><tr>" + "".join(
                f"<th{_style(idx)}>{_render_inline(cell)}</th>"
                for idx, cell in enumerate(header_cells)
            ) + "</tr></thead>")
            out.append("<tbody>")
            for row in body_rows:
                out.append("<tr>" + "".join(
                    f"<td{_style(idx)}>{_render_inline(cell)}</td>"
                    for idx, cell in enumerate(row)
                ) + "</tr>")
            out.append("</tbody></table>")
            continue

        quote_match = _QUOTE_LINE.match(stripped)
        if quote_match:
            flush_paragraph()
            flush_list()
            if quote_lines is None:
                quote_lines = []
            quote_lines.append(quote_match.group(1))
            i += 1
            continue

        list_match = _LIST_ITEM.match(line)
        if list_match:
            flush_paragraph()
            flush_quote()
            if list_items is None:
                list_items = []
            list_items.append((len(list_match.group(1)), list_match.group(2)))
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
            i += 1
            continue

        flush_list()
        flush_quote()
        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    flush_list()
    flush_quote()
    return "\n".join(out)
