# Claude for Researchers

A practical guide and toolkit for researchers — especially physicists — who want
to use [Claude Code](https://claude.ai/code) productively on long, technically
demanding projects.

This is written from real experience running a months-long mathematical research
project with Claude Code, not from a weekend experiment. It covers what works,
what wastes time, and what you should keep control of yourself.

---

## Table of Contents

1. [What Claude Code is good for in research](#what-claude-code-is-good-for-in-research)
2. [The most important file: CLAUDE.md](#the-most-important-file-claudemd)
3. [Solving the context-window problem: the condensed-notes pattern](#solving-the-context-window-problem-the-condensed-notes-pattern)
4. [Session continuity: next-session-prompts](#session-continuity-next-session-prompts)
5. [Skills: reusable procedures](#skills-reusable-procedures)
6. [Settings and hooks](#settings-and-hooks)
7. [Git workflow for academics](#git-workflow-for-academics)
8. [GitHub README and LaTeX](#github-readme-and-latex)
9. [Numerics and computation](#numerics-and-computation)
10. [Honest limitations](#honest-limitations)
11. [Templates and scripts in this repo](#templates-and-scripts-in-this-repo)

---

## What Claude Code is good for in research

**Good at:**
- Reading, editing, and compiling LaTeX — including tracking down obscure errors
- Writing and debugging Python, Mathematica/PARI-GP scripts for numerics
- Keeping track of what you've tried, what failed, and why (if you set it up right)
- Maintaining multiple related documents in sync (e.g., a full paper + a condensed reference)
- Git: committing, writing messages, managing dual remotes, resolving simple conflicts
- Translating your intent into working code faster than writing it yourself

**Not good at:**
- Original mathematical insight. It will confidently suggest wrong things.
- Remembering anything between sessions without explicit help (see below)
- Knowing when it's wrong. You must verify results independently.
- Replacing a collaborator or a referee

The right mental model: Claude is a very fast, very well-read junior researcher
who needs your supervision. It can do real work, but it doesn't know when it's
out of its depth.

---

## The most important file: CLAUDE.md

`CLAUDE.md` is a file at the root of your project that Claude reads at the start
of every session. It is the single most important thing you can configure. A
good `CLAUDE.md` makes every session productive from the first message. A bad
one — or a missing one — means you spend the first 20 minutes re-explaining your
project every time.

**What to put in it:**

```
# Project name and goal
One paragraph. What is this project, what is the mathematical/scientific object
you are studying, and what is the current open question?

# Key conventions
Notation that Claude must get right: what ξ(s) means, what your
normalizations are, which sign convention you use. Claude will use these
without you having to repeat them.

# File map
Which files exist, what each one is for, and — critically — which one is
the authoritative record. If you have a 300-page main document and a
20-page condensed reference, say so here and say which takes priority.

# Current status
A short, honest summary of where the project is RIGHT NOW. Not history —
current state. One screenful. Update this at the end of every session.

# Open tasks (ranked)
What is the next thing to do. If you don't write this, Claude will guess,
and it will guess wrong.

# Chat formatting
Tell Claude how you want math rendered in chat. Claude Code's chat does not
render LaTeX by default. You probably want: "write math in plain Unicode
(ξ, μ, ∑, ½) in chat replies; LaTeX only inside .tex files."

# Skills
List any skills you have defined (see below) and what they do.

# Writing style for your main document
If Claude is helping you write a paper, say what level of detail you want,
what to expand vs abbreviate, and what the document's purpose is.
```

**Anti-patterns to avoid:**
- Don't make it a logbook. Move finished work out of CLAUDE.md into a DONE log.
  CLAUDE.md should be navigable, not a timeline.
- Don't put everything in it. Long CLAUDE.md files slow Claude down and bury the
  important parts. Use the condensed-notes pattern for detailed content.
- Update the "Current status" section at the end of every session, before you close.
  If you forget, the next session starts confused.

See [`examples/CLAUDE-template.md`](examples/CLAUDE-template.md) for a starting template.

---

## Solving the context-window problem: the condensed-notes pattern

Claude has a finite context window. On a long project — a paper draft, a
multi-month calculation — your main document will eventually be too large for
Claude to hold in memory. This causes sessions to degrade: Claude forgets
earlier results, contradicts itself, or misses important constraints.

**The pattern:** maintain two documents in parallel.

- `main.tex` (or your main file): the authoritative, comprehensive record.
  Everything established goes here in full detail. Verbose. Never read in full
  by Claude.
- `condensed.tex` (or `notes.md`): a short (15–30 page / 1000–3000 line)
  self-contained reference. Theorems, key formulas, current results, open
  questions — but no pedagogy, no re-derivations, no history. Claude reads
  this at the start of new sessions.

The condensed document acts as a compressed session memory. When the main
document grows beyond what fits in context, Claude reads the condensed version
instead and stays oriented.

**Rules for the condensed document:**
1. It must be self-contained. Someone (or Claude) reading only this document
   should be able to reconstruct the current state of the project.
2. It does NOT need to be complete or pedagogical. Theorem statements without
   proofs are fine. Formulas without derivations are fine.
3. Sync it deliberately. After a significant result in the main document, update
   the condensed version. Don't let them drift.
4. Never put temporary or in-progress content in it. It reflects what is
   established, not what is being tried.

The `/sync-condensed` skill in this repo automates part of the sync step — it
checks which changes in the main document are "load-bearing" (new theorems,
corrected formulas) and propagates them.

See [`examples/condensed-notes-guide.md`](examples/condensed-notes-guide.md) for
what to include and what to skip.

---

## Session continuity: next-session-prompts

Claude's memory across sessions is imperfect. Even with CLAUDE.md updated, there
is context that lives in the conversation and doesn't survive. The fix is simple:
maintain a human-written file called `next-session-prompts.md`.

**What it contains:**
- A ranked list of tasks for the NEXT session, with enough context that you can
  paste one into Claude and it knows exactly what to do
- A DONE log: a timestamped record of what was completed and what the result was.
  This is the durable log; CLAUDE.md is the current-state snapshot.

**Format that works:**

```markdown
## Prompt A — [SHORT NAME] (NEXT)
Context: [one paragraph of what we're trying to do and why]
What to do: [precise instruction, including which file/section/equation]
Expected output: [what success looks like]

## DONE

### 2026-06-01 — [task name]
Result: [what was found/built/proved]
Files changed: [list]
```

The key discipline: at the end of every session, before closing, write or update
the top prompt in this file. Future you (or future Claude) will thank you.

See [`examples/next-session-prompts-template.md`](examples/next-session-prompts-template.md).

---

## Skills: reusable procedures

Claude Code supports "skills" — named, reusable instruction sets that you invoke
with a `/skill-name` command. Think of them as macros for Claude: instead of
explaining a multi-step procedure every time, you write it once and invoke it
by name.

**When to write a skill:**
- A procedure you will do more than twice
- A procedure with a checklist (compile + check errors + fix overfull boxes)
- A procedure where the order of steps matters

**Good examples for research:**
- `/latex-compile` — compile, catch errors, fix overfull hboxes, report page count
- `/sync-condensed` — propagate load-bearing changes from main doc to condensed notes
- `/verify-calculation` — run a specified check (residue test, boundary condition) against current results
- `/write-section` — draft a new section in your house style and append it

**What NOT to make a skill:**
- Things you only do once
- Vague tasks ("do analysis") — skills need a defined done-condition
- Tasks where the procedure genuinely varies each time

**Skill anatomy:**

```
# Skill name

## What this does
One sentence.

## When to invoke
Precise conditions. Don't say "when you need to compile" — say what
state the file should be in, what the input is, what success looks like.

## Steps
1. ...
2. ...

## Output
What Claude tells you when done.
```

Skills live in `.claude/skills/` in your project directory. See the skills
in this repo's `.claude/skills/` for working examples.

---

## Settings and hooks

Claude Code's `.claude/settings.json` controls two important things:

**Permissions:** what Claude can do without asking you. In a research project
the most useful permission is letting Claude run your standard tool commands
(pdflatex, python, git status) without a confirmation prompt every time.

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(pdflatex*)",
      "Bash(python numerics/*)"
    ]
  }
}
```

**Hooks:** shell commands that fire automatically at specific events. The most
useful for researchers:

*Pre-compact hook* — runs before Claude compresses the conversation. Use it to
save the current state of your CLAUDE.md and next-session-prompts so nothing
is lost when the context rolls over:

```json
{
  "hooks": {
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "echo '## Auto-saved before context compact' >> CLAUDE.md"
      }]
    }]
  }
}
```

*Post-push hook* — if you push to a primary remote (GitHub), automatically
mirror to a secondary remote (institution GitLab) under a different identity:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Bash(git push github*)",
      "hooks": [{
        "type": "command",
        "command": "scripts/push-gitlab.sh"
      }]
    }]
  }
}
```

See [`.claude/settings.json`](.claude/settings.json) for a fully annotated
generic configuration.

**Important:** hooks run silently. A hook that fails silently can cause
real problems. Always test hooks manually before relying on them, and document
what each hook does in your CLAUDE.md.

---

## Git workflow for academics

Academic projects have specific git needs that general guides don't cover:

**Dual-remote setup (personal + institution):**
Many researchers have a personal GitHub account and an institution GitLab.
You want the same repo on both, with commits attributed to different email
addresses. Here's the setup:

```bash
# Add both remotes
git remote add github  https://github.com/YOUR_GITHUB_USER/your-repo.git
git remote add gitlab  git@git.YOUR_INSTITUTION.ac.uk:YOUR_ID/your-repo.git

# Make main track github (your primary)
git branch --set-upstream-to=github/main main

# For institution (if protected branch / append-only):
# Use a sync branch: git checkout -B gitlab-sync gitlab/main
# Apply changes, commit with institution email, push to gitlab
```

Tell Claude the dual-remote setup in CLAUDE.md. Otherwise it will push to
the wrong remote, or push with the wrong email.

**Commit discipline:**
- Commit small and often. Claude can help you recover from mistakes much more
  easily when commits are small.
- Write commit messages that explain WHY, not just what changed.
- Never commit: `.env` files, API keys, large binary data, generated PDFs
  (unless they are the deliverable).

See [`scripts/git-push-both.sh`](scripts/git-push-both.sh) for a script that
handles dual-remote push with the right identities.

---

## GitHub README and LaTeX

GitHub renders math in Markdown using MathJax, but with a **strict allowlist**
of supported commands. Many standard LaTeX commands are blocked or render
incorrectly. Common failures:

| LaTeX | GitHub renders? | Fix |
|-------|----------------|-----|
| `\operatorname{Res}` | No | Use `\mathrm{Res}` |
| `\mathscr{F}` | No | Use `\mathcal{F}` |
| `\bm{v}` | No | Use `\mathbf{v}` |
| Display math `$$...$$` | Sometimes | Use fenced math blocks |
| Inline math `$...$` | Sometimes | Use `$\`...\``$` syntax |

**Best practice for inline math in GitHub README:**

```markdown
The function $`\xi(s) = \pi^{-s/2}\Gamma(s/2)\zeta(s)`$ satisfies ...
```

**Best practice for display math:**

````markdown
```math
M_3 = M_3^{\mathrm{bdry}} + g_{\mathrm{int}} + \mathcal{E}
```
````

**Never assume your LaTeX compiles in GitHub.** Write the README, push it,
and check it in a browser before treating it as done.

See [`scripts/readme-latex-check.sh`](scripts/readme-latex-check.sh) for a
script that catches the most common blocklisted commands.

---

## Numerics and computation

For research numerics, Claude works best when you make explicit choices:

**Choose a primary engine and stick to it.** Don't mix Python and Mathematica
ad hoc — pick one as primary and use the other only for independent
cross-checks. For numerical verification: Python + mpmath (arbitrary precision,
free, reproducible). For symbolic computation: Mathematica (but outputs are
hard to put in version control) or SageMath (open source).

**Precision discipline:**
- Always set precision explicitly (`mp.dps = 30` or whatever you need)
- State the precision in your output and in your CLAUDE.md
- A result is not validated until you've confirmed it at two different
  precision levels, or by two independent methods

**Validation before claims:**
Every numerical result should have a validation: a known special case,
a symmetry check, or an independent calculation. Ask Claude to do this
as part of the task, not as an afterthought.

**Keep a run log:**
Route all background computation output to a log file your editor can
watch (`tail -f numerics/run.log`). This lets you monitor long-running
computations without blocking your editor.

---

## Honest limitations

**Claude makes mistakes, including confident ones.** In a months-long project
you will find errors that Claude introduced and didn't flag. The fix is not
to trust less — it is to build validation into every step. Every formula
Claude writes should have a sanity check. Every number should have an
independent calculation.

**Claude does not understand your field.** It has read a lot of papers, but
it does not have physical intuition or mathematical taste. You must supply
both. When Claude suggests something that "feels wrong," your instinct is
probably right.

**Context limits are real.** On a long project, Claude will forget things
that happened early in the session, or in previous sessions. The condensed-notes
pattern and next-session-prompts mitigate this significantly, but do not
eliminate it. Build your workflow around this constraint, not against it.

**Agentic tasks are risky.** When you ask Claude to do something that involves
many steps autonomously (refactor a large file, run a computation and update
the paper based on results), errors compound. For anything consequential,
prefer small steps with your verification in between.

---

## Templates and scripts in this repo

| File | What it is |
|------|------------|
| [`examples/CLAUDE-template.md`](examples/CLAUDE-template.md) | Starting CLAUDE.md for a research project |
| [`examples/condensed-notes-guide.md`](examples/condensed-notes-guide.md) | What to put in a condensed reference document |
| [`examples/next-session-prompts-template.md`](examples/next-session-prompts-template.md) | Session log template |
| [`.claude/settings.json`](.claude/settings.json) | Annotated generic settings + hooks |
| [`.claude/skills/latex-compile.md`](.claude/skills/latex-compile.md) | LaTeX compile skill |
| [`.claude/skills/sync-condensed.md`](.claude/skills/sync-condensed.md) | Sync condensed notes skill |
| [`scripts/git-push-both.sh`](scripts/git-push-both.sh) | Dual-remote push script |
| [`scripts/readme-latex-check.sh`](scripts/readme-latex-check.sh) | GitHub README LaTeX compatibility check |

---

## License

MIT. Use, adapt, and share freely. If this helped your research workflow,
a mention is appreciated but not required.
