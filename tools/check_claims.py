#!/usr/bin/env python3
"""
check_claims.py — project-wide consistency scanner for Quantum Anchor
=====================================================================

WHY THIS EXISTS
---------------
This project has already produced two classes of documentation defect:

  1. RETRACTED CLAIMS STILL ASSERTED AS PROVEN. The Borg "100% clear" result was
     shown to be a circuit tautology and retracted in VALIDATION.md §9. It was
     nevertheless still marked "BIZONYÍTVA (hardveres)" in four other places.
  2. MEASUREMENT SCOPE OVERSTATEMENT. The IQM circuit-level result was described
     as "meas_level=0 equivalent" and "1024 bitstrings captured" when the
     memory field held only the first 10.

Both defects survived because nothing checked them. This scanner encodes the
known-bad phrasings as patterns, so a regression fails loudly.

It is a heuristic, not a proof. A clean run means "none of the KNOWN bad
phrasings are present" — not "all claims are correct".
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files that are published / citeable, so wording matters.
SCANNED = [
    "README.md",
    "docs/VALIDATION.md",
    "docs/HOPE-WP-2026-V1.2.md",
    "arxiv/quantum_anchor_v1.2.tex",
    ".zenodo.json",
    "CITATION.cff",
]

# Each rule: (name, regex, why it is wrong, severity)
# severity "hard" = factually false claim; "soft" = misleading wording.
RULES: list[tuple[str, re.Pattern[str], str, str]] = [
    (
        "pulse-level-available",
        re.compile(r"pulse-level access available", re.I),
        "Claims IQM pulse-level access is available. It was MEASURED as denied "
        "on the account tier in use (VALIDATION.md 7.8.8).",
        "hard",
    ),
    (
        "meas-level-0-equivalent",
        re.compile(r"meas[_ ]level\s*=\s*0 (?:equivalent|ekvivalens)", re.I),
        "get_memory() returns decoded bitstrings, not analog IQ data. It is "
        "NOT a meas_level=0 equivalent.",
        "hard",
    ),
    (
        "full-memory-claim",
        re.compile(r"1024 bitstrings? (?:captured|ment|számít|nyers)", re.I),
        "The IQM audit JSON stores only the first 10 memory bitstrings, not "
        "all 1024.",
        "hard",
    ),
    (
        "phase-formula-1e-9",
        re.compile(r"(?:4\.11|4,11)\s*\*\s*37e-9|4\.11\s*GHz\s*\*\s*37\s*ns\s*=\s*0\.4398\s*rad", re.I),
        "GHz*ns is already dimensionless cycles; multiplying by 1e-9 yields "
        "1.37e-7 rad instead of 0.4398 rad. The factor must not be present.",
        "hard",
    ),
    (
        "placeholder-doi",
        re.compile(r"10\.5281/zenodo\.(?:X+|0+|placeholder)", re.I),
        "A placeholder DOI can be copied into a real citation. Omit it instead.",
        "hard",
    ),
    (
        "retracted-as-proven",
        re.compile(r"100% clear.{0,120}BIZONYÍTVA", re.I | re.S),
        "The Borg 100% clear result was retracted as a circuit tautology "
        "(VALIDATION.md §9).",
        "hard",
    ),
    (
        "anchor-proven",
        re.compile(r"anchor (?:drive )?(?:compensation )?(?:IS )?PROVEN", re.I),
        "Anchor drive compensation is not proven by any measurement. Both "
        "anchor-on and anchor-off yield 0% clear.",
        "hard",
    ),
    (
        "tesseract-validated",
        re.compile(r"Tesseract 4-plane architecture valid", re.I),
        "The 4-plane architecture executes, but 20-reality synchronized "
        "selection is not demonstrated (11.62% global).",
        "soft",
    ),
    (
        "token-on-cli",
        re.compile(r"--token\s+[\"']?YOUR_TOKEN", re.I),
        "Documenting a CLI token argument encourages passing secrets on the "
        "command line, where they persist in shell history.",
        "hard",
    ),
    (
        "bize-iros-da",
        re.compile(r"src/anchor_measure_iqm_final\.py"),
        "The script lives at the repository root, not under src/.",
        "soft",
    ),
    (
        "garnet-qubit-count",
        re.compile(r"(?:Garnet|garnet)[^\n]{0,40}?\b20\s*Q\b", re.I),
        "The measured Garnet backend has 19 qubits, not 20.",
        "hard",
    ),
    (
        "gamma-zero-reachable",
        re.compile(r"(?:gamma|γ)\s*=\s*0\s+(?:hardver|hardware)(?:en|es)?\s*(?:elér|achiev|reach)", re.I),
        "gamma=0 is not an established hardware state; finite T1/T2 make it "
        "physically unreachable.",
        "hard",
    ),
]

# Numbers that are only correct WITH their stated denominator. A bare figure is
# not a defect; a bare figure presented as THE result is. These fire when the
# documented value is quoted without the caveat that makes it interpretable.
CONTEXTUAL_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "11.62-without-denominator",
        re.compile(r"11[.,]62\s*%"),
        "The 11.62% figure divides by the REQUESTED 1024 shots; the counts "
        "actually summed to 1016, which gives 11.71%. Quote the denominator "
        "alongside it.",
    ),
    (
        "11.71-without-denominator",
        re.compile(r"11[.,]71\s*%"),
        "The 11.71% figure is the correct one, but only against the 1016 "
        "returned shots. State the denominator.",
    ),
]


# Lines that legitimately discuss a retracted claim must still be allowed to
# MENTION it, as long as they mark it as retracted. We detect the retraction
# marker in the surrounding context and skip.
# The marker that frames a retracted claim. These headings and phrases
# introduce a citation of the OLD claim rather than asserting it.
RETRACTION_MARKERS = re.compile(
    r"visszavon|retract|tautol|retrakt|hamis| téves|false positive|"
    r"RÉSZLEGES|NEM igazolt|NOT PROVEN|NOT SHOWN|NOT MEASURED|"
    r"What Was Claimed|Previous Claim|mi volt az állítás|"
    r"korábbi állítás|a korábbi|Why It Was Wrong|"
    # A struck-through or explicitly-false quotation. A table that lists the
    # OLD claim in the left column and the measured reality in the right is the
    # corrected form; without this the scanner flags its own fix.
    r"~~|—\s*false\b|\bfalse\b(?!\s*positive)|téves\s*\||_false_", re.I)

# A rule fires on a phrase, but a phrase preceded by a negation is the OPPOSITE
# of a defect: "NOT a meas_level=0 equivalent" is the corrected wording. Without
# this, the scanner would fire on exactly the sentences written to fix a bug —
# and a linter that fires on the fix gets switched off within a week.
NEGATION = re.compile(
    r"\bnot\b|\bno\b|\bnever\b|\bincorrect\b|\bwrong\b|"
    r"is not|are not|cannot|must not|\bnem\b|\bnot(?:a| an| egy)\b", re.I)

# A percentage that was computed against a stated denominator is fully
# interpretable. These markers mean the reader is told what it was divided by —
# which is the only thing that makes such a figure meaningful.
DENOMINATOR_CONTEXT = re.compile(
    r"denominator|nevező|osztó|1016|1024\s*(?:shot|mérés|requested|kért)|"
    r"requested\s*shots?|actual\s*shots?|visszakapott|"
    # A parenthesised arithmetic form: "(74+45/1024)". The denominator is stated,
    # so the figure is fully interpretable even without the word "denominator".
    r"/\s*(?:1024|1016)\b", re.I)


def _is_negated(line: str, match: re.Match[str]) -> bool:
    """True when the matched phrase is negated within its own clause.

    Only the text since the last sentence/clause break is inspected, so a
    negation in a previous sentence cannot whitelist a real assertion in the
    next one.
    """
    prefix = line[:match.start()]
    for sep in (". ", "! ", "? ", "; ", "| ", " — "):
        pos = prefix.rfind(sep)
        if pos != -1:
            prefix = prefix[pos + len(sep):]
    return bool(NEGATION.search(prefix))


def scan_file(rel: str) -> list[tuple[str, int, str, str, str]]:
    path = ROOT / rel
    if not path.exists():
        return [("MISSING-FILE", 0, rel, "scanned file does not exist", "hard")]
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [("ENCODING", 0, rel, "file is not valid UTF-8", "hard")]

    findings: list[tuple[str, int, str, str, str]] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        for name, pattern, why, severity in RULES:
            match = pattern.search(line)
            if not match:
                continue
            # A NEGATED mention is the corrected wording, not a defect.
            if _is_negated(line, match):
                continue
            # A line that QUOTES the bad phrasing to correct it, retract it, or
            # list it as a previous claim is not itself a defect. The marker may
            # sit on the same line or an adjacent one, so span three lines.
            window = "\n".join(lines[max(0, idx - 2):idx + 2])
            if RETRACTION_MARKERS.search(window):
                continue
            findings.append((name, idx, rel, why, severity))

        for name, pattern, why in CONTEXTUAL_RULES:
            match = pattern.search(line)
            if not match:
                continue
            # The figure is only interpretable together with what it was
            # divided by. If the denominator is stated anywhere in the
            # surrounding text, the reader is not misled — so stay silent.
            # This is the difference between "11.62% appears" (true, harmless)
            # and "11.62% is presented as THE global balance" (misleading).
            window = "\n".join(lines[max(0, idx - 4):idx + 5])
            if DENOMINATOR_CONTEXT.search(window):
                continue
            if RETRACTION_MARKERS.search(window):
                continue
            findings.append((name, idx, rel, why, "soft"))

    return findings


def main() -> int:
    print("=" * 74)
    print("QUANTUM ANCHOR — PROJECT CLAIM CONSISTENCY SCAN")
    print("=" * 74)
    print()

    all_findings: list[tuple[str, int, str, str, str]] = []
    for rel in SCANNED:
        found = scan_file(rel)
        status = "clean" if not found else f"{len(found)} finding(s)"
        print(f"  {rel:<38} {status}")
        all_findings.extend(found)

    if not all_findings:
        print()
        print("[OK] No known-bad phrasing found in any published file.")
        print("     This means the documented defects have not regressed.")
        print("     It does NOT certify that every claim is correct.")
        return 0

    print()
    print("=" * 74)
    print(f"FINDINGS ({len(all_findings)})")
    print("=" * 74)
    for name, line_no, rel, why, severity in all_findings:
        print()
        print(f"[{severity.upper()}] {name}")
        print(f"  {rel}:{line_no}")
        print(f"  why: {why}")

    hard = sum(1 for f in all_findings if f[4] == "hard")
    print()
    print(f"hard={hard}  soft={len(all_findings) - hard}")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())