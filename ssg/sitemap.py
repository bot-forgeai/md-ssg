"""Render a sitemap.xml from a list of built pages."""
import datetime
from xml.sax.saxutils import escape


def _page_lastmod(page):
    """Parse a page's date field (YYYY-MM-DD) into YYYY-MM-DD, or None.

    Unlike RSS's pubDate, sitemap lastmod doesn't need RFC-822/timezone
    conversion -- the front-matter date format is already what's wanted.
    """
    date_str = page.get("date")
    if not date_str:
        return None
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
    return date_str


def render_sitemap(pages, base_url):
    """Build a sitemap.xml string for pages, linking into base_url.

    base_url is the site's public root (e.g. "http://example.com"); each
    page's loc is base_url + "/" + slug + ".html", matching feed.py's
    link construction.
    """
    root = base_url.rstrip("/")
    urls = []
    for page in pages:
        loc = f"{root}/{page['slug']}.html"
        url = ["<url>", f"<loc>{escape(loc)}</loc>"]
        lastmod = _page_lastmod(page)
        if lastmod:
            url.append(f"<lastmod>{lastmod}</lastmod>")
        url.append("</url>")
        urls.append("\n".join(url))

    urls_xml = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls_xml}\n"
        "</urlset>\n"
    )
