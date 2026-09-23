"""Build a static site: content/*.md -> output/*.html, plus an index page."""
import os
import shutil

from .content import load_pages
from .feed import render_rss
from .markdown import render as render_markdown
from .paginate import paginate, paged_filename, pagination_links
from .render import apply_template
from .sitemap import render_sitemap
from .tags import group_by_tag, parse_tags, slugify_tag

DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{{ title }}</title><link rel="stylesheet" href="static/style.css"></head>
<body>
<nav><a href="index.html">&larr; home</a></nav>
<main><article>
<h1>{{ title }}</h1>
<div class="meta">{{ date }} {{ tags }}</div>
{{ content }}
</article></main>
</body>
</html>
"""

DEFAULT_INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{{ title }}</title><link rel="stylesheet" href="static/style.css"></head>
<body>
<main>
<h1>{{ title }}</h1>
{{ content }}
</main>
</body>
</html>
"""

DEFAULT_TAG_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{{ title }}</title><link rel="stylesheet" href="../static/style.css"></head>
<body>
<nav><a href="../index.html">&larr; home</a></nav>
<main>
<h1>{{ title }}</h1>
{{ content }}
</main>
</body>
</html>
"""

DEFAULT_TAG_INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{{ title }}</title><link rel="stylesheet" href="../static/style.css"></head>
<body>
<nav><a href="../index.html">&larr; home</a></nav>
<main>
<h1>{{ title }}</h1>
{{ content }}
</main>
</body>
</html>
"""

DEFAULT_STYLE_CSS = """\
body {
  font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  max-width: 42em;
  margin: 2em auto;
  padding: 0 1em;
  line-height: 1.6;
  color: #222;
}
nav {
  margin-bottom: 1.5em;
}
nav a {
  text-decoration: none;
  color: #555;
}
h1, h2, h3 {
  line-height: 1.25;
  margin-top: 1.5em;
}
.meta {
  color: #777;
  font-size: 0.9em;
  margin-bottom: 1.5em;
}
a {
  color: #1a5fb4;
}
a:visited {
  color: #613583;
}
code {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  background: #f0f0f0;
  padding: 0.15em 0.35em;
  border-radius: 3px;
}
pre {
  background: #f0f0f0;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}
pre code {
  background: none;
  padding: 0;
}
.tok-keyword {
  color: #8250df;
  font-weight: 600;
}
.tok-string {
  color: #0a7d33;
}
.tok-comment {
  color: #6e7781;
  font-style: italic;
}
.tok-number {
  color: #b35900;
}
.tok-variable {
  color: #0550ae;
}
"""


def _read_template(templates_dir, name, fallback):
    path = os.path.join(templates_dir, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return fallback


def _is_draft(page):
    return str(page.get("draft", "")).strip().lower() in ("true", "yes", "1")


def _tag_links(tags, prefix):
    if not tags:
        return ""
    return " ".join(f'<a href="{prefix}{slugify_tag(t)}.html">{t}</a>' for t in tags)


def _write_tag_pages(pages, templates_dir, output_dir, site_title, page_size=None):
    """Write one or more listing pages per tag, plus a tags/index.html of all tags."""
    groups = group_by_tag(pages)
    if not groups:
        return

    tags_dir = os.path.join(output_dir, "tags")
    os.makedirs(tags_dir, exist_ok=True)
    tag_template = _read_template(templates_dir, "tag.html", DEFAULT_TAG_TEMPLATE)
    tag_index_template = _read_template(templates_dir, "tags_index.html", DEFAULT_TAG_INDEX_TEMPLATE)

    for tag, tag_pages in groups.items():
        base_filename = f"{slugify_tag(tag)}.html"
        chunks = paginate(tag_pages, page_size)
        total = len(chunks)
        for num, chunk in enumerate(chunks, start=1):
            links = "<ul>\n" + "\n".join(
                f'<li><a href="../{p["slug"]}.html">{p["title"]}</a> {p.get("date", "")}</li>'
                for p in chunk
            ) + "\n</ul>"
            links += pagination_links(num, total, lambda n, bf=base_filename: paged_filename(bf, n))
            context = {"title": f"Tag: {tag}", "content": links}
            html = apply_template(tag_template, context)
            out_name = paged_filename(base_filename, num)
            with open(os.path.join(tags_dir, out_name), "w", encoding="utf-8") as f:
                f.write(html)

    index_links = "<ul>\n" + "\n".join(
        f'<li><a href="{slugify_tag(tag)}.html">{tag}</a> ({len(tag_pages)})'
        for tag, tag_pages in groups.items()
    ) + "\n</ul>"
    index_context = {"title": f"Tags — {site_title}", "content": index_links}
    index_html = apply_template(tag_index_template, index_context)
    with open(os.path.join(tags_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)


def build_site(content_dir, templates_dir, output_dir, static_dir=None, site_title="My Site",
                base_url=None, drafts=False, page_size=None):
    """Render every content page plus an index, writing HTML into output_dir.

    If base_url is given, also writes an RSS feed to feed.xml and a
    sitemap to sitemap.xml -- both need absolute URLs, so they're
    skipped without one.

    A page with a front-matter `draft: true` field is excluded from the
    build (and the feed) unless drafts=True is passed.

    page_size, if given, splits the site index and each tag's listing
    page into pages of that many entries (page 1 keeps the original
    filename, e.g. index.html/tags/<tag>.html; page N>=2 becomes
    index2.html/tags/<tag>2.html, etc.), with simple prev/next links.
    None (the default) keeps the original single-page-per-listing
    behavior. The feed/sitemap always list every page regardless.

    Returns the list of page dicts that were built (useful for tests).
    """
    pages = load_pages(content_dir)
    if not drafts:
        pages = [p for p in pages if not _is_draft(p)]
    pages.sort(key=lambda p: p.get("date", ""), reverse=True)

    os.makedirs(output_dir, exist_ok=True)
    page_template = _read_template(templates_dir, "page.html", DEFAULT_TEMPLATE)
    index_template = _read_template(templates_dir, "index.html", DEFAULT_INDEX_TEMPLATE)

    for page in pages:
        html_body = render_markdown(page["body"])
        context = dict(page)
        context["content"] = html_body
        context["tags"] = _tag_links(parse_tags(page), "tags/")
        out_html = apply_template(page_template, context)
        out_path = os.path.join(output_dir, f"{page['slug']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out_html)

    index_chunks = paginate(pages, page_size)
    index_total = len(index_chunks)
    for num, chunk in enumerate(index_chunks, start=1):
        links = "<ul>\n" + "\n".join(
            f'<li><a href="{p["slug"]}.html">{p["title"]}</a> {p.get("date", "")}</li>'
            for p in chunk
        ) + "\n</ul>"
        links += pagination_links(num, index_total, lambda n: paged_filename("index.html", n))
        index_context = {"title": site_title, "content": links}
        index_html = apply_template(index_template, index_context)
        out_name = paged_filename("index.html", num)
        with open(os.path.join(output_dir, out_name), "w", encoding="utf-8") as f:
            f.write(index_html)

    _write_tag_pages(pages, templates_dir, output_dir, site_title, page_size)

    if static_dir and os.path.isdir(static_dir):
        dest = os.path.join(output_dir, "static")
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(static_dir, dest)

    style_path = os.path.join(output_dir, "static", "style.css")
    if not os.path.exists(style_path):
        os.makedirs(os.path.join(output_dir, "static"), exist_ok=True)
        with open(style_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_STYLE_CSS)

    if base_url:
        rss = render_rss(pages, site_title, base_url)
        with open(os.path.join(output_dir, "feed.xml"), "w", encoding="utf-8") as f:
            f.write(rss)

        sitemap = render_sitemap(pages, base_url)
        with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(sitemap)

    return pages
