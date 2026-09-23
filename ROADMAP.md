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
| 8 | GitHub Pages deploy helper | A documented workflow (or a bundled `.github/workflows/deploy.yml` template a site can copy) for publishing `ssg build`'s output to GitHub Pages. Removes a manual step for anyone actually using this to publish something. | Small — mostly documentation plus one workflow YAML template; no code changes to `ssg/` itself. |

## Shipped

| # | Item | PR |
|---|---|---|
| 1 | `sitemap.xml` generation | #6 |
| 2 | Table support in the markdown subset | #8 |
| 3 | Blockquote and nested-list support | #10 |
| 4 | Per-site config file (`ssg.toml`) | #12 |
| 5 | Syntax highlighting for fenced code blocks | #14 |
| 6 | Pagination for the index and tag-index pages | #16 |
| 7 | Custom 404 page support | #18 |

## Notes

- Items aren't in strict priority order — treat the table order as a
  first-pass guess, not a queue. Reorder freely.
- An item can be split, merged, or dropped without ceremony; this file
  isn't a spec, just a list of what to consider next.
- Completed items should move to a "Shipped" section below (once one
  exists) referencing the PR, rather than being deleted — keeps a
  record of what Phase 3 has actually delivered.
