# Spec: Spin off `ssg` into bot-forgeai/md-ssg + autonomous triage workflow

**Status:** Phase 0 (extraction) and Phase 1 (manifest + polling) done. Open
Decisions #1-5/#8 resolved 2026-09-12 (see §6) — Phase 2 (triage automation)
is ready to build.
**Audience:** an LLM coding agent (Claude Code / ForgeAI itself) that will execute this
**Source repo verified:** `https://github.com/bot-forgeai/forgeai-build` (cloned and inspected directly — see §1)

## 1. What's actually in the repo (verified, not assumed)

`forgeai-build` is a single monorepo, one `pyproject.toml`, one shared `tests/` directory, one shared CI workflow. It currently holds nine packages: `babble`, `eulerlib`, `quest`, `recall`, `shortlink`, `ssg`, `ttt`, `vitalsdash`, plus `tests/`. The README states outright: *"An autonomous agent's own build repo — commits and PRs here come from an unattended loop, merged only when its own CI passes."* That's already true for `ssg` today — no human-approval gate currently exists anywhere in this repo.

`ssg` specifics:
- Package: `ssg/` — `render.py`, `content.py`, `feed.py`, `markdown.py`, `tags.py`, `build.py`, `__main__.py`, plus a demo site under `ssg/site/` (2 sample posts, a template, a stylesheet).
- Tests: `tests/test_ssg.py` — lives in the shared top-level `tests/` dir, not inside the package. This has to move too.
- Zero third-party runtime dependencies — everything it imports is stdlib (`argparse`, `re`, `html`, `http.server`, `shutil`, `xml.sax.saxutils`, `email.utils`, `functools`, `datetime`, `os`, `sys`). The one dependency declared in the monorepo's `pyproject.toml` (`qrcode>=7.0`) belongs to a different package, not `ssg`.
- Packaging today: `ssg` is registered as one entry in a shared `pyproject.toml` whose `[project]` name is still `eulerlib` (a leftover from that being the first package added) — there's no per-package `pyproject.toml` anywhere in this repo. A standalone repo needs its own from scratch.
- Git history for `ssg` is small and completely clean: exactly 4 commits, all squash-merged PRs — `#50` (initial: markdown+front-matter→HTML), `#51` (RSS feed), `#52` (`--drafts` flag), `#53` (tag pages). `tests/test_ssg.py`'s history is identical (same 4 commits touch both).
- No LICENSE file, no CONTRIBUTING, no issue templates, no labels or issues visible anywhere in the repo — this session's GitHub access to this repo is read-only via plain git clone; the API (`api.github.com`) is not authorized for it here, so I could not check for existing issues/labels/PRs directly. Sergio or ForgeAI's own credentials would need to confirm whether any exist, but nothing in the repo's config suggests an issue-intake process is set up yet.

**Bottom line:** this is a very clean, low-risk extraction — small history, no dependencies, no coupling to other packages. The interesting design work is entirely in the workflow (§4-5), not the extraction mechanics.

## 2. Terminology this spec assumes (flag if wrong)

The original request used "bug PRs" and "feature request PRs." Given the repo has no issues/labels/contribution process today, this spec assumes both start as GitHub **Issues** (bug reports and feature requests aren't diffs), and ForgeAI is the one writing the actual PRs in response:

| Term as used | Assumed to mean |
|---|---|
| "bug PR" | An open GitHub **Issue** labeled `bug` |
| "feature request PR" | An open GitHub **Issue** labeled `enhancement` |
| "PR" (when ForgeAI acts) | An actual **Pull Request** ForgeAI opens containing a code diff |

If Sergio means real external contributors will open actual Pull Requests with diffs, the classification step is the same but "fix"/"implement" become *review and merge/request-changes* rather than *write the diff yourself* — that's Open Decision #1.

## 3. Goals / non-goals

**Goals:** `ssg` gets its own repo with real history, its own packaging, and its own CI. ForgeAI keeps developing it going forward. Bug reports get fixed without Sergio in the loop, gated on CI. Feature requests never get built without Sergio explicitly saying go, via a GitHub-native signal. Every autonomous action leaves a visible trail.

**Non-goals (this pass):** not building a generic "spin off any ForgeAI package" framework yet (Phase 4 sketches it once `ssg` proves the pattern); not touching how the other 8 packages in `forgeai-build` are managed; not deciding whether `ssg` accepts outside contributors (Open Decision #5).

## 4. Phased plan

### Phase 0 — Extract `ssg` into its own repo (done)

Concrete commands, based on the actual layout found in §1:

```bash
# 1. Fresh clone, filtered to just the two paths that matter
git clone https://github.com/bot-forgeai/forgeai-build.git ssg-extract
cd ssg-extract
git filter-repo --path ssg/ --path tests/test_ssg.py
# result: only the 4 commits (#50-#53) survive, ssg/ and tests/test_ssg.py
# land at the same relative paths — no renaming needed.

# 2. Add what a standalone repo needs (none of this exists per-package today):
#    - pyproject.toml: project name "md-ssg" (matches the repo name; the
#      importable package stays `ssg` — no code changes needed, same pattern
#      as e.g. beautifulsoup4/bs4), version 0.1.0, requires-python >=3.9,
#      NO runtime dependencies (verified zero third-party imports),
#      console script ssg = "ssg.__main__:main", package-data ssg = ["site/**/*"]
#    - README.md: lift the "## ssg" section straight out of forgeai-build's
#      current README — it's already accurate and complete
#    - .github/workflows/ci.yml: same shape as the monorepo's
#      (checkout -> setup-python 3.11 -> pip install -e . pytest -> pytest -q)
#    - LICENSE: MIT (confirmed — Decision #7 resolved)

# 3. Push to the new (empty) repo: bot-forgeai/md-ssg (confirmed — Decision #6 resolved)

# 4. Back in forgeai-build: remove ssg/ and tests/test_ssg.py, remove the
#    three ssg references in pyproject.toml (scripts entry, packages list,
#    package-data), replace the "## ssg" README section with a one-line
#    pointer to the new repo.
```

**Acceptance criteria:** new repo builds and runs standalone from a clean clone (`pip install -e . pytest && pytest -q` green); `git log --follow` on `ssg/build.py` in the new repo still shows all 4 original commits; `forgeai-build`'s own CI still passes after `ssg` is removed (the other 8 packages and their tests are untouched).

### Phase 1 — Register the new repo in ForgeAI's workflow (done)

1. Add a manifest (e.g. `managed-repos.yaml` in `forgeai-build`) listing repos ForgeAI manages beyond its own: repo URL, short description, triage policy reference, whether autonomous merge is allowed. This is what makes Phase 4 (generalizing to future spin-offs) cheap.
2. Wire ForgeAI's existing run loop to read the manifest and poll each listed repo's issues/PRs on whatever cadence it already uses for its own work — reuse the existing scheduler, don't add a second one.
3. **Acceptance criteria:** ForgeAI's loop demonstrably enumerates open issues on the new repo via the GitHub API (a log line or dry-run report is sufficient proof — no action needs to be taken yet).

### Phase 2 — Triage automation

For each new issue on the `ssg` repo ForgeAI hasn't processed yet (track with a `forgeai-seen` label to avoid reprocessing):

1. **Classify** by label if present (`bug`/`enhancement`); if unlabeled, ForgeAI reads the body and applies the label itself — gives Sergio a visible audit trail of how it categorized things.
2. **If `bug`:** branch, fix, open a PR (`Fixes #N`), gate on CI green. Auto-merge *only* if CI is green **and** the diff is a single file under ~50 changed lines with no CI/dependency-file changes (Decision #2, resolved). Otherwise leave it open and assign to Sergio.
3. **If `enhancement`:** don't write code yet. Post a comment with an implementation sketch (this is the "scope" step that makes approval meaningful), assign the issue to Sergio's GitHub account, apply `needs-approval`. Do nothing further until Sergio adds the `approved` label (Decision #3, resolved).
4. **On approval:** swap `needs-approval` → `in-progress`, implement on a branch, open a PR, gate on CI — but always wait for Sergio's manual merge on feature PRs even with CI green, since a feature is a design decision, not just a correctness question (Decision #4, resolved).
5. **Acceptance criteria:** one real bug issue and one real feature issue run end-to-end produce exactly the artifacts above with no manual step except the single approval action.

### Phase 3 — "Improve and expand" as its own ongoing mandate

Kept separate from reactive triage, since the intake source differs:

- A `ROADMAP.md` in the new repo (ForgeAI-maintained, Sergio-editable) lists candidate improvements.
- On a cadence, ForgeAI picks one item and routes it through the *same* approval gate as an external feature request (post plan → assign Sergio → wait for `approved` → implement) — same gate, different source.
- **Acceptance criteria:** one ForgeAI-originated roadmap item completes this path before calling Phase 3 done.

### Phase 4 — Generalize (later, optional)

Once this proves out, the manifest (Phase 1) and triage logic (Phase 2) should already be repo-agnostic — worth confirming that's actually true once `ssg`'s new repo is live and stable, rather than assuming it.

## 5. Guardrails

- Every autonomous change goes through a PR, never a direct push — bugs included, even though `forgeai-build` itself currently allows fully unattended merges.
- CI must be green before any autonomous merge; if the new repo somehow loses CI, that's a Phase 0 regression, not optional to fix later.
- Cap auto-merge to a defined diff size/scope; anything bigger gets a human look even for "just" a bug fix.
- Rate-limit autonomous PRs per run so a bad classification loop can't spam the repo.
- ForgeAI's GitHub actions (labels, comments, assignment, PRs, merges) should be attributable to a distinct identity, not indistinguishable from Sergio's own activity.

## 6. Open decisions — all resolved 2026-09-12

| # | Decision | Resolution |
|---|---|---|
| 1 | Do "bug/feature PRs" mean Issues, or real external PRs with diffs? | **Issues.** ForgeAI writes the fix/feature diff itself in response to an Issue — no outside contributors exist yet. |
| 2 | What diff size/scope qualifies a bug PR for auto-merge without Sergio? | **Small: single file, under ~50 changed lines, no CI/dependency-file changes.** Anything bigger gets a human look. |
| 3 | Concrete approval signal for a feature request? | **A specific label (`approved`) added by Sergio**, polled by ForgeAI. |
| 4 | Do feature PRs auto-merge on CI-green, or always wait for manual merge? | **Always wait for manual merge.** CI-green is necessary but not sufficient — a feature is a design call. |
| 5 | Does the new repo accept outside contributions? | **No — Sergio + ForgeAI only, for now.** Phase 2 doesn't need untrusted-input handling yet; revisit if that changes. |
| 6 | ~~New repo name and org?~~ | **Resolved: `bot-forgeai/md-ssg`** |
| 7 | ~~License for the new repo?~~ | **Resolved: MIT** |
| 8 | What GitHub identity does ForgeAI act as for issue/PR operations? | **Same `bot-forgeai` identity that already merges `forgeai-build`'s own PRs** — no new credential. |

## 7. Handoff — next step

Phase 0 and Phase 1 are both done, and all open decisions are resolved (see
§6). Phase 2 (triage automation) is ready to build against the rules above:
classify issues on `md-ssg`, auto-fix+merge small scoped bugs (≤1 file,
<50 lines, CI green, no CI/dependency-file changes), and for `enhancement`
issues post an implementation sketch + apply `needs-approval`, waiting for
Sergio's `approved` label before implementing — and even then always wait
for his manual merge, never auto-merge a feature PR.
