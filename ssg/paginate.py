"""Shared pagination helper for the site index and tag listing pages."""


def paginate(items, page_size):
    """Split items into chunks of page_size. None/0 means "no pagination"."""
    if not page_size:
        return [items]
    return [items[i:i + page_size] for i in range(0, len(items), page_size)]


def paged_filename(base_filename, page_num):
    """Page 1 keeps base_filename; page N>=2 becomes e.g. index2.html."""
    if page_num == 1:
        return base_filename
    name, ext = base_filename.rsplit(".", 1)
    return f"{name}{page_num}.{ext}"


def pagination_links(current, total, filename_for):
    """Render prev/next links for page `current` of `total`, or "" if just one page."""
    if total <= 1:
        return ""
    parts = []
    if current > 1:
        parts.append(f'<a href="{filename_for(current - 1)}">&larr; newer</a>')
    if current < total:
        parts.append(f'<a href="{filename_for(current + 1)}">older &rarr;</a>')
    return '\n<nav class="pagination">' + " | ".join(parts) + "</nav>"
