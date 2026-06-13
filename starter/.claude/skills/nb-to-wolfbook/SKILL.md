---
name: nb-to-wolfbook
description: "Convert Mathematica .nb or .m files to Wolfbook .wb format so they open and run in VS Code. Use when bringing existing .nb/.m files into Wolfbook, or to make an existing .wb bridge-safe."
---

# nb-to-wolfbook

Converts Mathematica files (.nb / .m) to Wolfbook `.wb` (a VS Code Notebook JSON),
and — critically — makes the resulting cells **bridge-safe** so they evaluate
identically through the Wolfbook MCP (`runCell` / `evaluateExpression`) as they do
in the Mathematica front end.

## When to invoke
`/nb-to-wolfbook <file-or-directory>`  — convert .nb/.m to .wb.
`/nb-to-wolfbook --fix-wb <file.wb>`   — normalize an EXISTING .wb in place (bridge-safe), backup written.

## ⚠️ The bug this skill exists to prevent (READ THIS)

A Wolfram cell can wrap **one statement over several physical lines**:

```
Eeqv[{j1_},{k1_}] := (-1)^(j1) j1!/(k1-1) Coefficient[
   GenSer, ep[j1,k1]];
MMVbar[j_,k_] := (-1)^(Total[j]+Length[j])
   MMV[j,k];
```

The front end parses each cell as one unit, so this is fine *interactively*. But an
evaluator that **splits a cell on newlines** (the Wolfbook MCP `runCell`, a headless
`Get` of re-serialised text, naive `ToExpression`) sees broken fragments and either:

- throws `Syntax::sntxi: Incomplete expression` (the `Sum[...,⏎{...}]` case), or
- treats the newline as **implicit `Times`**: `(-1)^k ⏎ MMV[...]` silently drops to a
  product / loses the `MMV` factor, and `def1;⏎def2;` becomes `Times[def1;, def2;]`
  instead of two definitions.

This corrupts the kernel **silently** — definitions look present but are wrong — and is
exactly what makes a cell-by-cell rebuild "unfaithful." The fix: put **each statement on
one physical line**, collapsing only the *intra-statement* newlines (insignificant
whitespace) and keeping a newline only after a top-level `;`. Semantics are unchanged,
comments are preserved, and the cell is now safe for any evaluator.

## Helper scripts (committed alongside this skill)

- `wl_normalize.py` — the normalizer. `normalize(code)` collapses intra-statement
  newlines; string/comment/bracket-aware. Also a CLI:
  `python3 wl_normalize.py --wb <file.wb>` rewrites every wolfram code cell in place
  (writes `<file>.wb.bak` first). Or pipe: `... | python3 wl_normalize.py`.
- `nb2wb_extract.wls` — wolframscript extractor: reads a `.nb` and emits every cell in
  order as **faithful InputText** via the front end (`FrontEnd`ExportPacket[..., "InputText"]`),
  preserving comments and special characters. Avoids the old lossy "Package export + split
  on blank lines," which destroyed cell boundaries.
- `nb2wb.py` — the driver: runs the extractor, normalizes code cells, writes the `.wb`.

## Steps for .nb files (preferred path — needs wolframscript)

```bash
python3 .claude/skills/nb-to-wolfbook/nb2wb.py "<file.nb>" ["<out.wb>"]
```

This produces a faithful, bridge-safe `.wb`. Report the printed summary line.

If `wolframscript` is unavailable, fall back to: open the notebook in Mathematica,
File → Save As → Package (.m), then use the `.m` steps below — but STILL run the
normalizer on the result (see below), or the multi-line bug persists.

## Steps for .m files

1. Read the file.
2. Split into cells: runs of ≥2 blank lines are cell boundaries; a block that is only a
   `(* === Title === *)`-style comment becomes a markdown cell, others are code cells.
3. **Normalize each code cell** with `wl_normalize.normalize` (bridge-safety — non-negotiable).
4. Write the `.wb` with `json.dumps(notebook, indent=1, ensure_ascii=False)`.

## .wb format reminders
- `kind: 2` = wolfram code cell (set `"languageId": "wolfram"`), `kind: 1` = markdown.
- 1-space indent; `value` a valid JSON string; `outputs: []`; UTF-8.
- Always build JSON with Python's `json` module, never by hand.

## Making an existing .wb safe (no reconversion)
```bash
python3 .claude/skills/nb-to-wolfbook/wl_normalize.py --wb "numerics/your-notebook.wb"
```
Normalizes every code cell in place (backup `.wb.bak`). Use this when a `.wb` already
exists but mis-evaluates through the bridge.

## Verify after conversion
Confirm no code cell still has a mid-statement line break (the bridge-unsafe pattern):
```python
def midline(v):  # any line ending in an operator / open bracket = continuation
    return any(l.rstrip().endswith(('+','-','*','/','/.','->',':>',',','**','(','[','{','=','^','@','/;','&&','||')) for l in v.split('\n'))
# expect 0 such code cells after normalize
```
Output format: `Converted: <src> -> <dst> (N code cells, M markdown cells, bridge-safe).`
If any file could not be converted, say which and why.
