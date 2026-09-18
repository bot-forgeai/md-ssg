# Roadmap

Candidate improvements for `md-ssg`, maintained by ForgeAI and freely
editable by the operator (Sergio) — add, remove, reorder, or edit the
scope of any item at any time; nothing here is a commitment until it's
actually picked up.

This is the intake list for Phase 3 of `TRIAGE-SPEC.md`: on its own
cadence, ForgeAI picks one item from here, posts an implementation
sketch as a comment on a new tracking issue, assigns the operator, and
waits for the same `approved` label used for external feature requests
before writing any code. Manual merge is always required, same as any
other feature PR — CI-green is necessary but never sufficient.

Every item below stays in the spirit of what `md-ssg` already is: a
small, dependency-free content pipeline, not a general-purpose site
framework. An item that would pull in a third-party runtime dependency
or meaningfully grow the surface area should say so explicitly and be
weighed against that tradeoff before it's approved.

## Candidates

| # | Item | Why | Rough scope |
|---|---|---|---|
| 3 | Blockquote and nested-list support | Same category as tables: real markdown people actually write that the current subset silently mangles or drops. | Medium — extends the existing block parser; nested lists are the fiddlier of the two. |
| 4 | Per-site config file (`ssg.toml` or similar) | Right now every build repeats `--title`/`--base-url`/etc. as CLI flags. A config file removes that repetition and is a more natural home for future per-site settings (e.g. item 6 below). | Medium — stdlib `tomllib` (3.11+) avoids a new dependency; needs a compatibility decision for the `requires-python >=3.9` floor in `pyproject.toml`. |
| 5 | Syntax highlighting for fenced code blocks | Code blocks currently render as plain monospace. Real highlighting usually means a third-party lexer (Pygments) — conflicts with the zero-dependency principle unless done as a small stdlib-only tokenizer for a handful of common languages. | Large, and the dependency tradeoff needs an explicit decision before scoping further. |
| 6 | Pagination for the index and tag-index pages | Today's index lists every page on one HTML file; fine for a small blog, awkward once a site has dozens of posts. | Medium — needs a page-size setting (natural fit for item 4's config file) and predictable page-N URLs. |
| 7 | Custom 404 page support | `serve` has no notion of a not-found page; a site providing `templates/404.html` (or similar) could get it copied/rendered into the build output. | Small — mirrors the existing template-fallback pattern already used for `page.html`/`index.html`. |
| 8 | GitHub Pages deploy helper | A documented workflow (or a bundled `.github/workflows/deploy.yml` template a site can copy) for publishing `ssg build`'s output to GitHub Pages. Removes a manual step for anyone actually using this to publish something. | Small — mostly documentation plus one workflow YAML template; no code changes to `ssg/` itself. |

## Shipped

| # | Item | PR |
|---|---|---|
| 1 | `sitemap.xml` generation | #6 |
| 2 | Table support in the markdown subset | #8 |

## Notes

- Items aren't in strict priority order — treat the table order as a
  first-pass guess, not a queue. Reorder freely.
- An item can be split, merged, or dropped without ceremony; this file
  isn't a spec, just a list of what to consider next.
- Completed items should move to a "Shipped" section below (once one
  exists) referencing the PR, rather than being deleted — keeps a
  record of what Phase 3 has actually delivered.
