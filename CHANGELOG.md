# Changelog

Notable, user-facing changes to this toolkit. This is a curated list of the
updates worth knowing about — not every commit (see the git history for that).
Useful for deciding whether to re-copy anything from `starter/` into a project
you set up from an earlier version.

Versioning is calendar-based (`vYYYY.MM`): this is a guide and a copy-in starter
pack, not a linked library, so there is no API to break — the version answers
"how current is my copy?", nothing more.

## v2026.06 — 2026-06-18 (update)

### Fixed
- **`verify-citation`, `reality-check`, `cross-validate` were missing their YAML frontmatter.**
  Without the `---\nname: ...\ndescription: ...\n---` block, Claude Code silently does not
  register these as slash commands — `/verify-citation` would not appear in the `/` menu and
  could not be invoked. Re-copy all three `SKILL.md` files from `starter/.claude/skills/`.

### Changed
- **`cross-validate` example generalised.** The Step 1 worked example used an Eisenstein series
  claim that was specific to one project. Replaced with a universally recognisable Gaussian
  integral example so the format is clear to any researcher.

---

## v2026.06 — 2026-06-13

First tagged release of the current structure. Everything below landed this month.

### Action needed if you set up a project before this release
- **Skills must use the folder format `skills/<name>/SKILL.md`.** A flat
  `skills/<name>.md` file is silently *not* registered as a slash command. If your
  skills are flat files, move each `<name>.md` to `<name>/SKILL.md`.
- The skills below were rewritten. If you copied earlier versions, re-copy them
  from `starter/.claude/skills/` to get the fixes.
- **Re-copy `nb-to-wolfbook` and `sync-wb-nb`** (see the `nb-to-wolfbook` entry under
  Fixed): an earlier copy can *silently drop a factor* from a display-wrapped
  definition during `.nb` → `.wb` conversion. Re-copy both skill folders from
  `starter/.claude/skills/`; if you installed `sync-wb-nb` globally, also replace
  `~/.claude/skills/sync-wb-nb/`. Then run
  `python3 .claude/skills/nb-to-wolfbook/wl_normalize.py --check <your.wb>` on existing
  notebooks — the gap was latent, so a notebook converted earlier may already be wrong.
- **Re-copy `latex-compile`** (see Changed): an earlier copy missed broken `\ref`/`\cite`
  warnings, so a compile could report clean while the PDF printed `??`/`[?]`. Re-copy
  `latex-compile` from `starter/.claude/skills/` (and replace `~/.claude/skills/latex-compile/`
  if you installed it globally), then recompile and confirm the broken-ref gate is clean.

### Added
- **Adaptive bootstrapping.** Both setup routes now install *by relevance* instead
  of installing everything: the README bootstrap prompt selects skills from your
  project description, and a new interactive `scripts/bootstrap.sh` asks a few
  questions and installs only what applies. The workbook / brief /
  next-session-prompts trio plus CLAUDE.md is the universal core; everything else
  is conditional.
- **Global skills** (`~/.claude/skills/`) documented — install a skill once and use
  it in every project; bootstrapping checks there before making a local copy.
- **Overleaf-via-git workflow** and the `overleaf-sync` skill, for collaborating on
  a shared Overleaf project from its git remote.
- **AI-output staging**: `numerics/generated/` and `figures/generated/` folders for
  Claude-produced outputs pending your review.
- **Wolfbook splitter fix**: `scripts/patch-wolfbook-splitter.py` patches a sharp edge in
  Wolfbook's cell evaluator — a `(* ... *)` comment right after an operator (`x :=(*note*)`
  with the RHS on the next line) hid the operator from the line-splitter, tearing one
  statement into two broken inputs (`Syntax::sntxi` + a bogus orphan evaluation). Idempotent,
  backs up, `--revert`able. Both bootstrap routes surface a zero-clone one-line installer
  (`curl … | python3 -`) for Mathematica projects. See
  [`docs/wolfbook-comment-split-fix.md`](docs/wolfbook-comment-split-fix.md).
- **Context-monitoring note** in the session-length section: the read-only `/context`
  (what's filling the window) and `/usage` (where tokens/cost go) commands, plus a rule
  of thumb — glance at ~50%, act by ~70%, don't wait for auto-compaction, and for
  research prefer a fresh session seeded from your documents over repeated (lossy)
  compaction.
- **`wolfram-headless` skill** for reliable heavy headless `wolframscript`. It encodes
  two hard-won lessons: (1) `The product exited because of a license error` is almost
  always a mis-reported kernel **crash** (a memory spike), not a licensing problem — so
  it shows how to confirm the licence then shrink the computation; and (2) literal Greek
  in a `.wls` file **silently corrupts symbols** under `wolframscript`'s non-UTF-8 read,
  so always use ASCII escapes (`\[Omega]` …). Ships `scripts/greek2esc.py` (convert a
  file in one pass) and an opt-in `hooks/wolfram-license-notice.sh` that auto-flags the
  misleading error. `scripts/bootstrap.sh` installs it for Mathematica/wolframscript
  projects (and now fetches every skill's helper scripts, not just the SKILL.md).

### Changed
- **`latex-compile`** rewritten: compiles with `pdflatex` and captures stdout
  (avoiding the `latexmk` stale-log trap), greps with `-a` (pdflatex embeds binary
  bytes that silently defeat plain grep), uses correct severity thresholds, and
  reformats rather than rewords when fixing overfull boxes.
- **`latex-compile` now catches broken `\ref`/`\cite`.** The issue grep matched only
  capital `Undefined` (the fatal *control sequence* error) and so missed the lowercase
  broken-reference/citation *warnings* (`Reference 'x' … undefined`, `Citation 'x' …
  undefined`) — meaning a dead `\ref` could ship as `??` and a dead `\cite` as `[?]`
  while the run reported clean. The pattern is now `[Uu]ndefined`, plus key-mismatch
  diagnosis (used vs. defined keys) and a **mandatory broken-ref gate** that must report
  zero undefined refs/cites before the skill claims success.
- **`sync-wb-nb`** gained a `regenerate` mode that rebuilds a whole `.nb` from its
  `.wb` with proper syntax colouring and section headings — for new or
  fully-rewritten notebooks, alongside the existing cell-by-cell sync.
- **`nb-to-wolfbook`** rewritten to make every converted cell *bridge-safe*: each
  statement goes on one physical line, so the tool that runs cells from VS Code
  cannot silently mis-evaluate a statement that was wrapped across several lines.
  The line-boundary detector handles the tricky Wolfram cases — postfix `&`
  (`Function`) ends a statement while `&&` continues it, `/;` (`Condition`) and `/.`
  continue, `2.` (a number) ends, and backslash-continued long numbers/strings
  (e.g. high-precision values, `*^-76` exponents) re-join with no inserted space.
  Ships helper scripts (`nb2wb.py`, `nb2wb_extract.wls`, `wl_normalize.py`).
- **Permissions model** in `starter/.claude/settings.json`: allow routine commands,
  *ask* before anything dangerous (including `sudo`/`mkfs`/`fdisk`/`shred`), block
  nothing outright — so Claude never stalls but always pauses before a risky action.
- Templates consolidated into `starter/` (the old `examples/` folder was retired);
  the `sync-condensed` skill was renamed `sync-brief`.
- The **dual-remote mirror hook is now opt-in** (off by default). It was a silent
  trap before — see Fixed.

### Fixed
- **`nb-to-wolfbook` could silently drop a factor from a display-wrapped definition.**
  The bridge-safety detector decided line breaks by how a line *ended*. A wide
  definition that the Mathematica front end *display-wrapped* onto an indented next
  line ends in a complete value (e.g. `…)`), so the detector mistook the wrap for a
  statement boundary, split the definition, and silently dropped the trailing factor —
  no error, a wrong definition. `wl_normalize` now also treats a newline followed by a
  *continuation indent* as a wrap (genuine statement breaks start at column 0), and
  ships a hazard checker — `wl_normalize.py --check <file.wb>` (exit 1 on any
  definition split across a top-level newline), run automatically by `nb2wb.py` and by
  `sync-wb-nb regenerate` before it overwrites a `.nb`.
- **Silent dual-remote mirror hook.** The starter's `settings.json` shipped an
  *active* `PostToolUse` hook running `scripts/git-push-both.sh`, but the starter
  didn't include that script — so a copied project appeared to mirror pushes to a
  second remote (e.g. institution GitLab) while silently doing nothing. The hook now
  ships **off** (empty `PostToolUse`), the `git-push-both.sh` template is included
  under `starter/scripts/`, and both bootstrap routes enable it only if you say you
  use two remotes, with the exact block to paste documented in `settings.json`.

### Clarified
- The opening of the guide now states its scope explicitly: this is a workspace and
  workflow toolkit to make *your* research faster, not a system for getting Claude
  to conduct research autonomously.
