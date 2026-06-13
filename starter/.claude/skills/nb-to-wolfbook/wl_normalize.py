#!/usr/bin/env python3
"""Normalize Wolfram cell text so every statement is on ONE physical line:
collapse newlines that occur inside brackets or mid-statement into spaces;
keep a newline only right after a top-level ';'. String- and comment-aware.
This makes cells safe for line-splitting evaluators (e.g. MCP runCell) and
removes the newline-as-implicit-Times ambiguity, without changing semantics."""
import sys, re

def normalize(code: str) -> str:
    out = []
    depth = 0          # () [] {} nesting
    i = 0
    n = len(code)
    in_str = False
    comment_depth = 0
    while i < n:
        c = code[i]
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
            # find last non-space emitted char
            j = len(out) - 1
            while j >= 0 and out[j] in ' \t': j -= 1
            last = out[j] if j >= 0 else ''
            if depth == 0 and last == ';':
                # statement boundary: keep a single newline
                while out and out[-1] in ' \t': out.pop()
                out.append('\n')
                # skip following whitespace/newlines
                i += 1
                while i < n and code[i] in ' \t\r\n': i += 1
                continue
            else:
                # mid-statement: collapse to a single space
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
