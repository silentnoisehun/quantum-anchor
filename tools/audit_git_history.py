#!/usr/bin/env python3
"""
audit_git_history.py — secret-leak audit across the ENTIRE git history
=======================================================================

audit_secrets.py scans the working tree. That is not enough: a credential can
have been committed and later deleted, in which case the working tree is clean
while the object database still holds the secret and the remote already has it.

This script walks every blob reachable from every ref and applies the same
patterns. Blobs are streamed via `git cat-file --batch` so a large history
does not have to be checked out.

CRITICAL: this script NEVER prints a secret value. Findings are reported as
<commit-ish>:<path> plus a redacted preview. Running the audit must not become
a second distribution channel for the credential.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CREDENTIAL-ASSIGNED-LITERAL", re.compile(
        r"(?:IQM_TOKEN|IBM_QUANTUM_API_TOKEN|GITHUB_TOKEN|GH_TOKEN|"
        r"OPENAI_API_KEY|ANTHROPIC_API_KEY|BRAKET_MW_TOKEN)"
        r"\s*[:=]\s*[\"']([^\"']{8,})[\"']", re.I)),
    ("BEARER-TOKEN", re.compile(r"Bearer\s+([A-Za-z0-9\-_.]{12,})")),
    ("CLI-TOKEN-LITERAL", re.compile(
        r"--token\s+[\"']?([A-Za-z0-9\-]{12,})", re.I)),
]

PLACEHOLDER = re.compile(
    r"your|placeholder|x{3,}|changeme|todo|<|>|example|dummy|redacted|"
    r"none|null|\$\{|\$\(|%s|\{[a-z_]+\}", re.I)

TEXTY = re.compile(
    r"\.(py|md|json|tex|cff|ya?ml|toml|cfg|ini|sh|ps1|txt)$")


def git(*args: str) -> str:
    res = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    return res.stdout


def redact(v: str, keep: int = 3) -> str:
    return (f"{v[:keep]}...{v[-keep:]} ({len(v)} chars)"
            if len(v) > keep * 2 else "*" * len(v))


def main() -> int:
    print("=" * 74)
    print("GIT HISTORY SECRET AUDIT — Quantum Anchor")
    print("=" * 74)
    print()

    revs = git("rev-list", "--all").split()
    if not revs:
        print("[!] no commits found; nothing to audit")
        return 0
    print(f"commits to audit : {len(revs)}")

    # Build a blob -> paths index from `git ls-tree -r` per commit.
    blob_paths: dict[str, set[str]] = {}
    for rev in revs:
        for line in git("ls-tree", "-r", "--format=%(objectname) %(path)",
                        rev).splitlines():
            if not line.strip():
                continue
            sha, _, path = line.partition(" ")
            blob_paths.setdefault(sha.strip(), set()).add(path.strip())
    print(f"unique blobs     : {len(blob_paths)}")
    print()

    print("=== streaming blob contents ===")
    shas = list(blob_paths.keys())
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
        errors="replace",
    )
    assert proc.stdin and proc.stdout
    proc.stdin.write("\n".join(shas) + "\n")
    proc.stdin.flush()

    findings: list[tuple[str, str]] = []
    for _ in shas:
        header = proc.stdout.readline()
        if not header:
            break
        parts = header.split()
        # "<sha> <type> <size>" for real blobs. Missing objects come back as
        # "<sha> missing" and must be skipped, not parsed.
        if len(parts) < 3 or parts[1] != "blob":
            if len(parts) >= 2 and parts[1] != "blob":
                # Missing/absent object: cat-file emitted no body to consume.
                continue
            continue
        try:
            size = int(parts[2])
        except ValueError:
            # Defensive: any unexpected header shape ends this blob's stream.
            continue
        body = proc.stdout.read(size)
        proc.stdout.read(1)          # trailing newline

        paths = blob_paths.get(parts[0], set())
        relevant = [p for p in paths if TEXTY.search(p)]
        if not relevant:
            continue
        try:
            text = body
        except Exception:
            continue

        for name, pat in PATTERNS:
            for m in pat.finditer(text):
                value = m.group(1)
                if not value or PLACEHOLDER.search(value):
                    continue
                for p in sorted(relevant):
                    findings.append((name, f"{p} :: {redact(value)}"))

    try:
        proc.stdin.close()
        proc.wait(timeout=30)
    except Exception:
        proc.kill()

    # De-duplicate: the same secret in the same path across many commits is
    # one leak, not N leaks.
    unique = sorted(set(findings))

    if not unique:
        print("[OK] No credential material found in any committed blob.")
        print("     Combined with audit_secrets.py, the repository history is")
        print("     clear of the credential patterns this project cares about.")
        return 0

    print("=" * 74)
    print(f"FINDINGS ({len(unique)}) — values redacted by design")
    print("=" * 74)
    for name, detail in unique:
        print(f"  [{name}] {detail}")
    print()
    print("ACTION: if any value above is real, treat it as compromised —")
    print("rotate the credential, then rewrite history before publishing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())