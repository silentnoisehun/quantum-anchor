#!/usr/bin/env python3
"""Static LaTeX sanity check — no LaTeX toolchain required.

Checks the structural invariants that most often break when a .tex file is
edited in place: balanced environments, balanced braces, and math-mode dollar
parity. It cannot prove the document compiles (that needs pdflatex/tectonic),
but it catches the class of damage that a text edit actually produces.
"""
import re
import sys
from pathlib import Path

DOC = Path(sys.argv[1] if len(sys.argv) > 1
           else r"C:\Users\mater\Documents\orassh\quantum_anchor\arxiv\quantum_anchor_v1.2.tex")

text = DOC.read_text(encoding="utf-8")

# Environments, ignoring escaped \{ and \{
env_begin = re.findall(r"\\begin\{(\w+\*?)\}", text)
env_end = re.findall(r"\\end\{(\w+\*?)\}", text)

print(f"file: {DOC.name}")
print(f"begin: {len(env_begin)}   end: {len(env_end)}")
print()

fails = 0
print("=== environment balance ===")
for env in sorted(set(env_begin) | set(env_end)):
    b = env_begin.count(env)
    e = env_end.count(env)
    status = "ok" if b == e else "MISMATCH"
    if b != e:
        fails += 1
    print(f"  {env:<14} begin={b:<3} end={e:<3} {status}")

# Braces: count only unescaped ones
ob = len(re.findall(r"(?<!\\)\{", text))
cb = len(re.findall(r"(?<!\\)\}", text))
print()
print("=== braces ===")
print(f"  open={ob}  close={cb}  {'ok' if ob == cb else 'MISMATCH'}")
if ob != cb:
    fails += 1

# Dollar parity, ignoring \$ and inside verbatim-ish lines
dollars = len(re.findall(r"(?<!\\)\$", text))
print()
print("=== math mode ===")
print(f"  unescaped $ count = {dollars}  {'ok (even)' if dollars % 2 == 0 else 'ODD -> unbalanced math mode'}")
if dollars % 2 != 0:
    fails += 1

# \label / \ref sanity
labels = set(re.findall(r"\\label\{([^}]+)\}", text))
refs = set(re.findall(r"\\ref\{([^}]+)\}", text))
missing = refs - labels
print()
print("=== cross references ===")
print(f"  labels={len(labels)} refs={len(refs)}")
if missing:
    print(f"  WARNING unresolved refs: {sorted(missing)}")
else:
    print("  all refs resolve")

print()
print("RESULT:", "FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)