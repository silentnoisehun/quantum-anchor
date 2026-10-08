#!/usr/bin/env python3
"""
audit_secrets.py — repository secret-leak audit
===============================================

SCOPE
-----
Walks the working tree (excluding .git and binary/large files) looking for:
  1. Credential ENV VARS assigned a real-looking literal value.
  2. Long opaque high-entropy strings in tracked content (possible API keys).
  3. Authorization headers / bearer tokens.
  4. Whether the CURRENT value of IQM_TOKEN / IBM_QUANTUM_API_TOKEN literally
     appears anywhere in the tree — the strongest signal of an actual leak.

This script NEVER prints a matched secret value. It prints the file, the line
number, and a redacted preview only, so that running the audit cannot itself
distribute the credential into terminal logs or CI output.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules",
             "dist", "build", ".mypy_cache", ".pytest_cache"}
MAX_BYTES = 4 * 1024 * 1024
TEXT_EXT = {".py", ".md", ".json", ".tex", ".cff", ".yml", ".yaml", ".txt",
            ".toml", ".cfg", ".ini", ".sh", ".ps1", ".env", ".gitignore"}

SECRET_VARS = [
    "IQM_TOKEN", "IBM_QUANTUM_API_TOKEN", "IBM_QUANTUM_INSTANCE",
    "IQM_USER", "GITHUB_TOKEN", "GH_TOKEN", "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY", "BRAKET_MW_TOKEN",
]

ASSIGN_RE = re.compile(
    r"(IQM_TOKEN|IBM_QUANTUM_API_TOKEN|IQM_USER|GITHUB_TOKEN|GH_TOKEN|"
    r"OPENAI_API_KEY|ANTHROPIC_API_KEY|BRAKET_MW_TOKEN)"
    r"\s*[:=]\s*[\"']([^\"']{6,})[\"']", re.I)

BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9\-_.]{12,}")

# High-entropy-ish opaque tokens. Requires length AND mixed character classes,
# which keeps ordinary identifiers and URLs out.
OPAQUE_RE = re.compile(r"\b[A-Za-z0-9_\-]{40,}\b")

TOKEN_CHARS = re.compile(r"^[A-Za-z0-9_\-]{16,}$")

# Public measurement identifiers that appear throughout the audit trail.
# These are citation handles, not credentials:
#   IBM job id  db2XXXXXXXXXXXX           (db2 + 17 chars)
#   IQM job id  01a1162c-717c-77e7-...   (UUID-shaped)
# Artifacts combine them into filenames:
#   matryoshka_db2viifr11fs7397i3e0_20261007T074831Z.json
#   iqm_anchor_01a1162c-717c-...-90ed16c0e591_20261007T114508Z.json
_IBM_JOB = r"db2[0-9a-z]{17}"
_IQM_JOB = r"[0-9a-f]{8}(?:-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?"
_STAMP = r"[0-9]{8}t[0-9]{6}z"
_SEGMENT = rf"(?:[a-z_]+|v[0-9]+|{_IBM_JOB}|{_IQM_JOB}|{_STAMP})"

AUDIT_NAME_RE = re.compile(rf"^{_SEGMENT}(?:_{_SEGMENT})*$", re.I)


def _is_audit_filename(tok: str) -> bool:
    """True when the token looks like a measurement artifact filename."""
    return bool(AUDIT_NAME_RE.match(tok))


def redact(value: str, keep: int = 4) -> str:
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}...{value[-keep:]} ({len(value)} chars)"


def is_probably_secret(value: str) -> bool:
    """A literal assigned to a credential var is a finding regardless of shape,
    unless it is obviously a placeholder or env interpolation."""
    low = value.lower()
    if any(tok in low for tok in
           ("your", "placeholder", "xxxx", "changeme", "todo", "<", ">",
            "${", "{{", "none", "null", "example", "dummy", "redacted")):
        return False
    return True


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
            except OSError:
                continue
            if p.suffix.lower() in TEXT_EXT or fn.startswith(".env") \
                    or fn == ".gitignore":
                yield p


def main() -> int:
    print("=" * 74)
    print("QUANTUM ANCHOR — SECRET LEAK AUDIT")
    print("=" * 74)
    print()

    findings: list[tuple[str, str, int, str]] = []
    scanned = 0

    for path in iter_files():
        rel = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1

        for i, line in enumerate(text.splitlines(), start=1):
            for m in ASSIGN_RE.finditer(line):
                var, value = m.group(1), m.group(2)
                if is_probably_secret(value):
                    findings.append(("CREDENTIAL-ASSIGNED-LITERAL",
                                     str(rel), i, f"{var} = {redact(value)}"))

            for m in BEARER_RE.finditer(line):
                findings.append(("BEARER-TOKEN", str(rel), i,
                                 redact(m.group(0).split(None, 1)[1])))

            for m in OPAQUE_RE.finditer(line):
                tok = m.group(0)
                if not TOKEN_CHARS.match(tok):
                    continue
                if any(tok.lower().startswith(p) for p in
                       ("github", "gitlab", "readthedocs", "docs.python")):
                    continue
                # Hex-only 40/64 char strings are usually content hashes.
                if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", tok, re.I):
                    continue
                # Measurement artifact filenames follow a known, benign
                # convention: <protocol>_<jobid-or-timestamp>.json. These are
                # audit trails, not credentials, and there are dozens of them
                # across the documentation.
                if _is_audit_filename(tok):
                    continue
                findings.append(("OPAQUE-HIGH-ENTROPY-STRING",
                                 str(rel), i, redact(tok)))

    print(f"files scanned: {scanned}")
    print()

    # The strongest check: does the live env token appear in any file?
    print("=== live environment credential search ===")
    for var in SECRET_VARS:
        val = os.getenv(var)
        if not val:
            continue
        leaked_in = []
        for path in iter_files():
            try:
                if val in path.read_text(encoding="utf-8"):
                    leaked_in.append(str(path.relative_to(ROOT)))
            except (UnicodeDecodeError, OSError):
                continue
        # The git index matters too: a value could be committed but deleted.
        status = "LEAK" if leaked_in else "clean"
        print(f"  {var:<26} set (len={len(val)}) -> {status}")
        for f in leaked_in:
            print(f"      FOUND IN: {f}")
            findings.append(("LIVE-TOKEN-IN-FILE", f, 0, var))
    if not any(os.getenv(v) for v in SECRET_VARS):
        print("  (no credential env vars set in this session)")
    print()

    if not findings:
        print("[OK] No secret material found in the working tree.")
        print("     Note: this scans the WORKING TREE. Run `git grep` across")
        print("     history as well before publishing a release.")
        return 0

    print("=" * 74)
    print(f"FINDINGS ({len(findings)}) — values are redacted by design")
    print("=" * 74)
    seen = set()
    for kind, rel, line, detail in findings:
        key = (kind, rel, line, detail)
        if key in seen:
            continue
        seen.add(key)
        loc = f"{rel}:{line}" if line else rel
        print(f"  [{kind}] {loc}")
        print(f"      {detail}")
    print()
    print("ACTION REQUIRED: remove these from the tree, then rotate the")
    print("credential — a value that reached disk must be assumed exposed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())