# md-ssg

ssg is a small static site generator: a filesystem content pipeline
that turns markdown files with a lightweight front-matter header into
plain static HTML you can host anywhere. It has zero third-party
runtime dependencies — everything it uses is Python stdlib.

It parses markdown files with a lightweight front-matter header,
renders them through a subset markdown-to-HTML converter, applies them
to `{{ placeholder }}` templates, and writes plain static HTML.

## Install

```
python3 -m venv .venv && .venv/bin/pip install -e .
```

## Usage

```
.venv/bin/ssg --site ssg/site new "My First Post"
.venv/bin/ssg --site ssg/site --title "My Blog" build
.venv/bin/ssg --site ssg/site --title "My Blog" serve --port 8000
```

A site directory holds `content/` (markdown files, front matter like
`title:`/`date:`, searched recursively), an optional `templates/`
(`page.html` and `index.html`; falls back to a built-in default when
missing), and an optional `static/` copied as-is into the build
output — if a site's own `static/` has no `style.css`, a small
built-in default (system fonts, code-block styling, no color scheme)
is written to `static/style.css` so the default templates aren't
unstyled; a site's own `static/style.css` always takes precedence.
`build` writes one HTML file per content page plus an
`index.html` listing every page sorted newest-first by `date`.
`serve` builds and then serves the output directory over a local
HTTP server (binds to `127.0.0.1` by default; pass `--host 0.0.0.0`
for a LAN-reachable demo). `new TITLE` scaffolds a dated front-matter
stub under `content/posts/`.

The markdown subset covers headers, paragraphs, unordered lists
(nestable by indentation), blockquotes, GFM-style tables (with
`:---`/`:-:`/`---:` alignment), fenced code blocks, and inline
`**bold**`/`*italic*`/`` `code` ``/`[links](url)` — enough for real
prose, not a CommonMark-complete parser. Raw HTML in content is
escaped, not executed. Nested blockquotes (`>>`) aren't a separate
nesting level — they're kept as flat content of the outer quote.

## Config file

A site directory can hold an optional `ssg.toml` at its root instead
of repeating `--title`/`--base-url`/`--drafts` on every command:

```toml
[site]
title = "My Blog"
base_url = "https://example.com"
drafts = false
```

Precedence is CLI flags > `ssg.toml` > built-in defaults — a flag
always wins if given, otherwise the config value is used, otherwise
the built-in default (`title = "My Site"`, no base URL, drafts
excluded). A malformed `ssg.toml` produces a clean `error: ...`
message and a non-zero exit rather than a traceback. Requires Python
3.11+ (uses the stdlib `tomllib` module — no new dependency).

## RSS feed and sitemap

Pass `--base-url` (a global flag, before the subcommand) to also
write an RSS 2.0 `feed.xml` and a `sitemap.xml` alongside the built
pages, e.g. `ssg --site ssg/site --base-url https://example.com build`.
Both need an absolute URL for their links, so they're skipped without
one. `sitemap.xml` follows the [sitemaps.org](https://www.sitemaps.org/)
protocol: one `<url>` per page, with `<lastmod>` when a page's front
matter has a `date` field.

## Drafts

A page marked `draft: true` in its front matter is excluded from the
build, the index, the feed, and the sitemap by default; pass the
global `--drafts`
flag (e.g. `ssg --site ssg/site --drafts serve`) to include drafts too,
for local preview before publishing. `new TITLE --draft` scaffolds a
new post already marked as a draft.

## Tags

A page's front-matter `tags:` field (a comma-separated string, e.g.
`tags: python, tutorial`) generates a listing page per tag under
`tags/<tag>.html` plus a `tags/index.html` linking every tag with its
page count; the default page template links each of a page's own tags
back to its tag listing. Sites with no tagged pages get no `tags/`
directory at all.

## Watch mode

`ssg --site ssg/site watch` rebuilds once, then polls `content/`,
`templates/`, and `static/` for changes (added, removed, or edited
files) and rebuilds again on each change, until interrupted with
Ctrl+C. `serve --watch` runs the same polling rebuild in a background
thread alongside the HTTP server, so editing a post and reloading the
browser shows the new content without restarting anything. `--interval`
sets the poll period in seconds (default: 1.0) for either mode.

## Development

```
python3 -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/pytest -q
```

## Origin

ssg shipped as one of several small, deliberately different build-lane
projects from an autonomous coding loop (ForgeAI), across 5 merged
PRs — initial build, RSS, drafts, tag pages, and watch mode — each
with its own test suite and green CI. This repo is ssg extracted from
that monorepo (`bot-forgeai/forgeai-build`) to stand on its own, with
its own packaging, history, and CI, so it can keep being developed
independently going forward.

## License

MIT — see [LICENSE](LICENSE).
