#!/usr/bin/env python3
"""Normalize Wolfram cell text so every statement is on ONE physical line:
collapse newlines that occur inside brackets or mid-statement into spaces;
keep a newline only right after a top-level ';'. String- and comment-aware.
This makes cells safe for line-splitting evaluators (e.g. MCP runCell) and
removes the newline-as-implicit-Times ambiguity, without changing semantics."""
import sys, re

def _strip_trailing(s: str) -> str:
    """Drop trailing whitespace and trailing (* ... *) comments (possibly several,
    possibly nested) so we can see the real last token of the line."""
    i = len(s)
    while True:
        while i > 0 and s[i-1] in ' \t': i -= 1
        if i >= 2 and s[i-2:i] == '*)':
            depth = 1; i -= 2
            while i > 0 and depth > 0:
                if i >= 2 and s[i-2:i] == '*)': depth += 1; i -= 2
                elif i >= 2 and s[i-2:i] == '(*': depth -= 1; i -= 2
                else: i -= 1
            continue
        break
    return s[:i]

def _is_continuation(out) -> bool:
    """True if the already-emitted current line ends mid-statement (the next
    physical line continues it), so the intervening newline must be collapsed.
    False if the line ends a complete statement (newline = statement boundary).
    Trailing comments are ignored (the operator may sit just before a comment)."""
    s = _strip_trailing(''.join(out))
    if not s:
        return False
    c = s[-1]
    c2 = s[-2] if len(s) >= 2 else ''
    if c == ';':
        return c2 == '/'          # '/;' Condition -> continuation; ';' -> statement end
    if c == '&':
        return c2 == '&'          # '&&' -> continuation; postfix '&' (Function) -> complete
    if c == '.':
        return not c2.isdigit()   # '/.' / Dot -> continuation; '2.' (a number) -> complete
    # binary operators, comma, and open brackets all require more input:
    return c in '+-*/^@<>=|~:,([{'

def normalize(code: str) -> str:
    out = []
    depth = 0          # () [] {} nesting
    i = 0
    n = len(code)
    in_str = False
    comment_depth = 0
    while i < n:
        c = code[i]
        # Wolfram backslash line-continuation: '\' at end of a physical line joins
        # to the next line with NO separator (used to split long numbers/strings,
        # e.g. high-precision Λ values and *^-76 exponents). Must not insert a space.
        if c == '\\' and i + 1 < n and code[i+1] in '\r\n':
            i += 2
            while i < n and code[i] in ' \t': i += 1
            continue
        if in_str:
            out.append(c)
            if c == '\\' and i+1 < n:
                out.append(code[i+1]); i += 2; continue
            if c == '"': in_str = False
            i += 1; continue
        if comment_depth > 0:
            if code[i:i+2] == '(*': comment_depth += 1; out.append('(*'); i += 2; continue
            if code[i:i+2] == '*)': comment_depth -= 1; out.append('*)'); i += 2; continue
            # collapse newlines inside comments to spaces too
            out.append(' ' if c in '\r\n' else c); i += 1; continue
        if c == '"': in_str = True; out.append(c); i += 1; continue
        if code[i:i+2] == '(*': comment_depth = 1; out.append('(*'); i += 2; continue
        if c in '([{': depth += 1; out.append(c); i += 1; continue
        if c in ')]}': depth -= 1; out.append(c); i += 1; continue
        if c in '\r\n':
            # Decide: is this newline a statement boundary (KEEP) or a
            # mid-statement continuation (collapse to a space)?
            #  - depth>0 (inside brackets)                         -> continuation
            #  - current line ends in a binary/operator/comma/opener -> continuation
            #  - FE soft-wrap: newline FOLLOWED BY a continuation indent
            #    (spaces/tabs then more code, not a blank line)     -> continuation.
            #    The front end's "InputText" export wraps a single wide expression
            #    this way, e.g.  "(-1)^(Total[j]+Length[j])\n   MMV[j,k,w]"  -- the
            #    leading indent is the tell-tale that the next line CONTINUES the
            #    statement (here by implicit Times). A line ending in a complete value
            #    like ')' fools the operator heuristic above, so without this check the
            #    newline survives and SPLITS the statement (the MMVbar bug: the MMV
            #    factor was silently dropped). Genuine statement breaks export at
            #    column 0 (no indent), so they are still kept.
            #  - otherwise (complete statement, next line at col 0) -> boundary, keep
            j = i + 1
            while j < n and code[j] in ' \t': j += 1
            indented = j > i + 1                        # whitespace after the newline
            blank = (j >= n) or (code[j] in '\r\n')     # nothing / blank line follows
            if depth > 0 or _is_continuation(out) or (indented and not blank):
                if out and out[-1] not in ' \t\n': out.append(' ')
            else:
                while out and out[-1] in ' \t': out.pop()
                out.append('\n')
            i += 1
            while i < n and code[i] in ' \t\r\n': i += 1
            continue
        out.append(c); i += 1
    # squeeze runs of spaces (outside strings already handled char-by-char; do a light pass)
    return ''.join(out)

def _depth0_segments(code: str):
    """Split code into segments at TOP-LEVEL (bracket depth 0) newlines, ignoring
    newlines inside (), [], {}, strings, and (* *) comments. Returns the non-blank
    segments — i.e. the individual statements the bridge would evaluate."""
    segs, cur = [], []
    depth = 0; i = 0; n = len(code); in_str = False; cdepth = 0
    while i < n:
        c = code[i]
        if in_str:
            cur.append(c)
            if c == '\\' and i+1 < n: cur.append(code[i+1]); i += 2; continue
            if c == '"': in_str = False
            i += 1; continue
        if cdepth > 0:
            if code[i:i+2] == '(*': cdepth += 1; cur.append('(*'); i += 2; continue
            if code[i:i+2] == '*)': cdepth -= 1; cur.append('*)'); i += 2; continue
            cur.append(c); i += 1; continue
        if code[i:i+2] == '(*': cdepth = 1; cur.append('(*'); i += 2; continue
        if c == '"': in_str = True; cur.append(c); i += 1; continue
        if c in '([{': depth += 1; cur.append(c); i += 1; continue
        if c in ')]}': depth -= 1; cur.append(c); i += 1; continue
        if c in '\r\n' and depth == 0:
            segs.append(''.join(cur)); cur = []; i += 1; continue
        cur.append(c); i += 1
    segs.append(''.join(cur))
    return [s for s in segs if s.strip()]

def _toplevel_flags(seg: str):
    """Scan a single segment at depth 0 (outside strings/comments) and report whether
    it contains a SetDelayed ':=', an assignment-or-comparison '=' (any, including
    '=='), or a ';'. Conservative: counting '==' as '=' only makes the B-side 'bare'
    test stricter (fewer false hazards)."""
    setdelayed = eq = semi = False
    depth = 0; i = 0; n = len(seg); in_str = False; cdepth = 0
    while i < n:
        c = seg[i]
        if in_str:
            if c == '\\' and i+1 < n: i += 2; continue
            if c == '"': in_str = False
            i += 1; continue
        if cdepth > 0:
            if seg[i:i+2] == '(*': cdepth += 1; i += 2; continue
            if seg[i:i+2] == '*)': cdepth -= 1; i += 2; continue
            i += 1; continue
        if seg[i:i+2] == '(*': cdepth = 1; i += 2; continue
        if c == '"': in_str = True; i += 1; continue
        if c in '([{': depth += 1; i += 1; continue
        if c in ')]}': depth -= 1; i += 1; continue
        if depth == 0:
            if seg[i:i+2] == ':=': setdelayed = True; i += 2; continue
            if c == '=': eq = True
            elif c == ';': semi = True
        i += 1
    return setdelayed, eq, semi

def _ends_semicolon(seg: str) -> bool:
    return _strip_trailing(seg.rstrip()).rstrip().endswith(';')

def find_split_hazards(code: str):
    """Detect the bug class behind the MMVbar regression: a DEFINITION whose RHS got
    split across a top-level newline, leaving an orphan factor/term on the next line
    (which the front end and any line-splitting evaluator both read as a SEPARATE
    statement, silently dropping it). Returns a list of (before, after) statement
    pairs. A pair is flagged when the earlier statement contains ':=' (a definition),
    does not end in ';', and the next statement is a BARE expression (no ':=', no '=',
    no ';' of its own) — i.e. it looks like a continuation of the definition rather
    than a statement in its own right. Conservative by design: legitimate ';'-separated
    or '='-bearing multi-statement cells are not flagged."""
    segs = _depth0_segments(code)
    hazards = []
    for a, b in zip(segs, segs[1:]):
        a_sd, a_eq, a_semi = _toplevel_flags(a)
        b_sd, b_eq, b_semi = _toplevel_flags(b)
        bs = b.strip()
        b_is_comment = bs.startswith('(*') and bs.endswith('*)')
        if a_sd and not _ends_semicolon(a) and not (b_sd or b_eq or b_semi) and not b_is_comment:
            hazards.append((a.strip(), b.strip()))
    return hazards

def check_wb(path: str):
    """Report split-statement hazards in every wolfram code cell of a .wb.
    Returns a list of (cell_index, before, after)."""
    import json
    nb = json.load(open(path, encoding="utf-8"))
    found = []
    for idx, c in enumerate(nb.get("cells", [])):
        if c.get("languageId") == "wolfram" or c.get("language") == "wolfram" or c.get("kind") == 2:
            for a, b in find_split_hazards(c.get("value", "")):
                found.append((idx, a, b))
    return found

def fix_wb(path: str) -> int:
    """Normalize every wolfram code cell of an existing .wb in place (backup first).
    Returns the number of cells changed. Also warns on any residual split hazard."""
    import json, shutil
    shutil.copy(path, path + ".bak")
    nb = json.load(open(path, encoding="utf-8"))
    changed = 0
    for c in nb.get("cells", []):
        if c.get("languageId") == "wolfram" or c.get("language") == "wolfram" or c.get("kind") == 2:
            v = c.get("value", "")
            nv = normalize(v)
            if nv != v:
                c["value"] = nv; changed += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(nb, indent=1, ensure_ascii=False))
    haz = check_wb(path)
    if haz:
        sys.stderr.write(f"WARNING: {len(haz)} split-statement hazard(s) remain after normalize:\n")
        for idx, a, b in haz[:10]:
            sys.stderr.write(f"  cell {idx}: ...{a[-50:]!r}  ⏎SPLIT⏎  {b[:50]!r}...\n")
    return changed

if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--wb':
        n = fix_wb(sys.argv[2])
        print(f"normalized {n} code cells in {sys.argv[2]} (backup: {sys.argv[2]}.bak)")
    elif len(sys.argv) >= 3 and sys.argv[1] == '--check':
        haz = check_wb(sys.argv[2])
        if not haz:
            print(f"OK: no split-statement hazards in {sys.argv[2]}")
        else:
            print(f"HAZARD: {len(haz)} split-statement site(s) in {sys.argv[2]}:")
            for idx, a, b in haz:
                print(f"  cell {idx}: ...{a[-60:]!r}  ⏎SPLIT⏎  {b[:60]!r}...")
            sys.exit(1)
    else:
        txt = sys.stdin.read()
        sys.stdout.write(normalize(txt))
