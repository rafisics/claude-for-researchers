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
            #  - depth>0 (inside brackets)            -> continuation
            #  - current line ends in a binary/operator/comma/opener -> continuation
            #  - otherwise (complete statement)       -> boundary, keep newline
            if depth == 0 and not _is_continuation(out):
                while out and out[-1] in ' \t': out.pop()
                out.append('\n')
            else:
                if out and out[-1] not in ' \t\n': out.append(' ')
            i += 1
            while i < n and code[i] in ' \t\r\n': i += 1
            continue
        out.append(c); i += 1
    # squeeze runs of spaces (outside strings already handled char-by-char; do a light pass)
    return ''.join(out)

def fix_wb(path: str) -> int:
    """Normalize every wolfram code cell of an existing .wb in place (backup first).
    Returns the number of cells changed."""
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
    return changed

if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--wb':
        n = fix_wb(sys.argv[2])
        print(f"normalized {n} code cells in {sys.argv[2]} (backup: {sys.argv[2]}.bak)")
    else:
        txt = sys.stdin.read()
        sys.stdout.write(normalize(txt))
