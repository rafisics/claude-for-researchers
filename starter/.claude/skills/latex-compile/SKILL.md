---
name: latex-compile
description: Compile a LaTeX document, fix all errors and overfull boxes cleanly. Use this instead of running pdflatex manually — it avoids the latexmk stale-log trap and silent grep failures on binary log output.
---
# latex-compile

Compile a LaTeX document, fix errors and overfull hboxes, and report a clean result.

## When to invoke
After any edit to a .tex file. Also invoke before committing.

## Input
The user may specify a file: `/latex-compile brief.tex`. Default: `workbook.tex`.
Work from the project root (wherever CLAUDE.md lives).

## 1. Compile — always force a real pass

**Critical:** never use `latexmk` to capture warnings. When `latexmk` decides targets
are up-to-date it skips compilation entirely; the `.log` it leaves is then **stale**
and will under-report (or zero-out) overfull warnings. Always force a real `pdflatex`
pass and capture from its **stdout**, not the `.log` file:

```
pdflatex -interaction=nonstopmode <file> > /tmp/tex.txt 2>&1
```

Run **twice** when cross-references, TOC, or forward `\ref`s changed. Warnings are
then current.

**Always use `grep -a`.** pdflatex embeds binary font-path bytes in its output, so
plain `grep` silently treats the file as binary and matches nothing. Every grep below
uses `-a`.

## 2. Fix fatal errors first

```
grep -anE "^! |LaTeX Error|Undefined control sequence|Runaway argument|Emergency stop" /tmp/tex.txt
```

The `! ...` line and the `l.<N>` line below it locate the fault. Common causes:
- **Undefined control sequence** → check macro definitions / `\newcommand` spelling
- **Missing `{` or `}`** → stray brace; count braces around the offending line
- **Missing `$`** → stray character in math, or fragile macro in section title
  → use `\DeclareRobustCommand` or `\texorpdfstring`
- **`\begin{X}` without `\end{X}`** → find the unclosed environment
- **`File not found`** → missing `\usepackage` or missing dependency

Fix in source, recompile, repeat until the fatal-error grep returns nothing.

## 3. Triage overfull \hbox warnings by severity

Overfulls come in three flavors — `in paragraph at lines N--M`, `in alignment at
lines N--M`, and `detected at line N` (math/box mode). Capture all three:

```
grep -a "Overfull" /tmp/tex.txt \
  | grep -aoE "\([0-9.]+pt too wide\).*(at lines [0-9]+(--[0-9]+)?|at line [0-9]+)" \
  | sort -t'(' -k2 -rn
```

Triage by overrun magnitude:
- **> 10pt** — visibly runs off the page → fix
- **5–10pt** — noticeable → fix if quick, otherwise note
- **< 5pt** — below visual threshold → leave; `\emergencystretch=3em` in the preamble absorbs these

Read the target location (use `Read` with offset) before editing to see whether it is
prose, inline math, a display equation, or a table. A `detected at line N` warning
points at the *closing* line of a math environment (`\end{align}`, `\]`), so the
offending wide row is typically a line or two **above** N.

## 4. Fix rules — REFORMAT, never reword

**Hard rule: do not change mathematical content, wording, table data, or abbreviate
headers to make things fit.** Content edits silently lose load-bearing text. Fix
overflow only by changing *layout*:

- **Inline math `$...$` that overruns** → promote to display `\[ ... \]`
- **Long single-line display** → break before a relational operator (`=`, `\le`,
  `\to`, …). In an `align`: insert `\notag\\` then `& \quad` continuation.
  **Preserve the `\label` and equation number** — put `\notag` only on the
  continuation line, never on the labelled line.
- **Long boxed equation** → `\boxed{\begin{aligned} ... \end{aligned}}`
- **Wide table** → `\small`, `\footnotesize`, or `\resizebox{\textwidth}{!}{...}`.
  Do NOT abbreviate column headers or cell content.
- **Overflowing prose paragraph** → wrap in `\begin{sloppypar}...\end{sloppypar}`
- **Single wide inline token** with no break point → `\allowbreak` at a factor
  boundary, or promote to display

## 5. Verify

After fixes, recompile with `pdflatex` (same `> /tmp/tex.txt` capture) and re-run
the step-3 grep on the **fresh** stdout. Confirm targeted overfulls are gone or < 5pt,
and that no new `! ` errors were introduced.

## 6. Report

```
Compiled <file>: N pages.
Errors fixed: <list or "none">
Overfull fixes: <list with rule used, or "none">
Remaining warnings: <list or "none — log is clean">
```

If a warning is genuinely unavoidable, say so and explain why it is harmless.
