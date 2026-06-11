---
name: sync-wb-nb
description: Propagate changes made in a Wolfbook .wb notebook into the paired Mathematica .nb file, keeping them in sync. Use after editing or adding cells in any .wb. The .wb is authoritative; the .nb is the mirror kept for collaborators who use Mathematica desktop.
---
# sync-wb-nb

Propagate a change made in a Wolfbook `.wb` notebook into the paired Mathematica `.nb`
notebook, so the two stay identical in content. We edit and test in the `.wb` (via the
Wolfbook MCP); the `.nb` is the mirror kept for collaborators who work in Mathematica.

## When to invoke
After editing or adding cells in a `.wb`. Add a line to your CLAUDE.md like:
> Always run `/sync-wb-nb` immediately after editing or adding cells in any `.wb`.

## Input
`/sync-wb-nb path/to/file.wb` — syncs that file and its paired `.nb` (same basename,
same directory). If no argument is given, ask the user which file to sync.

## Direction and source of truth
`.wb` → `.nb`. The `.wb` is authoritative. Never sync the other way here
(use `/nb-to-wolfbook` for the initial `.nb` → `.wb` conversion).

## Hard rules

- **Back up the `.nb` first** (`cp` to `/tmp`). Abort and restore if any verification fails.
- **Never splice raw text into the `.nb`.** Mathematica's `.nb` format maintains an internal
  byte-offset cache; a plain text edit leaves it stale and corrupts the file. Always use the
  Import → modify → Export round-trip via wolframscript (see Method below).
- **Keep synced code cells pure code.** Mathematica's parser discards `(* … *)` comments when
  converting code to boxes, so a code cell with a leading comment would silently lose it in
  the `.nb`. Put explanatory notes in a *separate* comment-only cell or in the workbook,
  not inline in a code cell that must round-trip.
- **Read cell text from the `.wb` JSON, never retype it.** That guarantees the `.nb` gets
  exactly the `.wb` content.
- **Verify, don't trust.** After inserting, re-import the `.nb` and assert the new cell's
  parsed expression `===` the `.wb` cell's parsed expression. Cell count must change by
  exactly the number of cells added.

## Method

### 1. Identify what changed in the `.wb`

Read the `.wb` JSON (it is plain text). Identify which cell(s) were added or edited.
Get a stable anchor in the `.nb`: find the `ExpressionUUID` of the cell that should
*precede* the new/edited cell. Search the `.nb` text for a distinctive substring of
that preceding cell's code, then read its `ExpressionUUID->"…"`.

> Note: a UUID appears twice in the raw `.nb` — once in the cell expression and once
> in the trailing `(* Internal cache information *)` index. The Import'd Notebook
> expression contains it once only. Anchor on the imported expression, not raw text.

### 2. Insert (or replace) via wolframscript — Import → rule → Export

```wolfram
dir = "<absolute path to the directory containing the files>";
nbfile = dir <> "<name>.nb";
wbfile = dir <> "<name>.wb";

wb = Import[wbfile, "RawJSON"];
(* read the exact code text of the changed cell from the .wb JSON *)
code = SelectFirst[wb["cells"],
         StringContainsQ[#["value"], "<unique snippet from that cell>"] &]["value"];

nb = Import[nbfile];
nBefore = Count[nb, _Cell, Infinity];

(* parse code text → Input boxes WITHOUT evaluating the definitions *)
boxes = ToExpression[code, StandardForm,
          Function[e, MakeBoxes[e, StandardForm], HoldAllComplete]];
newCell = Cell[BoxData[boxes], "Input", ExpressionUUID -> CreateUUID[]];

anchorUUID = "<ExpressionUUID of the preceding cell>";
(* INSERT after the anchor: *)
newnb = nb /. (c : Cell[___, ExpressionUUID -> anchorUUID, ___]) :>
              Sequence[c, newCell];
(* — or REPLACE an existing cell:
   newnb = nb /. Cell[___, ExpressionUUID -> targetUUID, ___] :> newCell *)

nAfter = Count[newnb, _Cell, Infinity];
If[nAfter - nBefore =!= 1, Print["ABORT: delta=", nAfter - nBefore]; Exit[1]];
Export[nbfile, newnb];
```

### 3. Verify

```wolfram
nb = Import[nbfile];
exprNb = ToExpression[
   SelectFirst[Cases[nb, Cell[BoxData[b_], "Input", ___] :> b, Infinity],
     StringContainsQ[ToString[#, InputForm], "<unique snippet>"] &],
   StandardForm, HoldComplete];
exprWb = ToExpression[code, StandardForm, HoldComplete];
Print["match: ", exprNb === exprWb, "  valid: ", Head[nb] === Notebook];
```

Both must print `True`. If either prints `False`, restore the backup and investigate.

## Notes

- `HoldAllComplete` ensures definitions are parsed to `RowBox` input cells and never
  evaluated during conversion. Multi-definition cells parse to `CompoundExpression`
  and round-trip correctly.
- Markdown cells (`kind: 1` in the `.wb`) map to `Cell[text, "Text"]` (or
  `"Section"`/`"Subsection"`) in the `.nb`. Mirror the style of neighbouring text
  cells in the existing `.nb`.
- wolframscript requires absolute paths — quote them if the path contains spaces
  or special characters.
- If wolframscript is not available, tell the user: the sync cannot be automated
  without a Mathematica licence. They will need to apply the change manually in
  Mathematica desktop.

## Output

```
Synced: <name>.wb → <name>.nb
  Cells added: N (cell count: M → M+N)
  Verification: match=True, valid=True
```

If verification fails, report which assertion failed and that the backup was restored.
