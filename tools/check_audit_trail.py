#!/usr/bin/env python3
"""
check_audit_trail.py — prove the published audit-trail claims against the FILES
===============================================================================

WHY THIS EXISTS
---------------
The documentation makes a concrete, checkable statement about the repository's
own artefacts:

    "All raw data in measurement_raw/ with job IDs, counts, backend properties,
     transpiled QASM."

check_claims.py cannot verify that. It matches phrasings in prose; it does not
open the JSON files. So the statement survived a claim audit that had
systematically found other false claims in this project.

It was FALSE. Measuring the directory instead of reading the sentence showed
that of the 28 records, 27 carry `transpiled_qasm` and `backend_properties`,
and exactly one — the IQM Garnet run — carries neither, because the saving code
of that run never wrote those blocks. The same file's `memory` field holds only
the first 10 of the returned bitstrings.

That is the general failure this tool closes: a documented property of a data
directory is only as trustworthy as the last time anyone measured it. Prose
review does not re-measure. This does.

WHAT IT CHECKS
--------------
For every `*.json` under `measurement_raw/`:

  1. It parses as JSON.
  2. It carries a job identifier.
  3. It carries counts.
  4. It reports whether `transpiled_qasm` and `backend_properties` are present,
     and totals them across the directory.
  5. It counts the `memory` entries and compares them against the `counts` total
     where both are present, so a truncated-memory record is detected rather
     than assumed complete.

It then cross-checks the MEASURED directory state against what the published
documents CLAIM, and fails if a document asserts uniformity the data does not
support.

The exit code is non-zero when a document overstates the artefacts. An
incomplete record is NOT itself an error — incomplete evidence is a legitimate
state to be in. The error is claiming it is complete.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

# Windows consoles default to cp1250 and cannot encode the box characters and
# Hungarian accents below. Without this the tool crashes on a SUCCESSFUL run,
# which is the worst possible time to crash.
for _name in ("stdout", "stderr"):
    _stream = getattr(sys, _name, None)
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "measurement_raw"

# Keys under which the records store these things. Records were written by
# several different scripts over time, so accept the known variants rather than
# assuming one schema — a false "missing" here would be its own kind of lie.
JOB_ID_KEYS = ("job_id", "jobId", "id")
COUNTS_KEYS = ("counts", "counts_raw")
QASM_KEYS = ("transpiled_qasm",)
BACKEND_PROPS_KEYS = ("backend_properties", "backend_props")

# Documents that make a repository-wide audit-trail claim.
CLAIMING_DOCS = (
    "README.md",
    "docs/VALIDATION.md",
    "docs/HOPE-WP-2026-V1.2.md",
    "arxiv/quantum_anchor_v1.2.tex",
    ".zenodo.json",
)

# A claim of UNIFORMITY: every record has the field. These are the phrasings
# that are only true if all files agree.
UNIVERSAL_CLAIM_PATTERNS = (
    re.compile(r"all raw data.{0,160}transpiled", re.IGNORECASE | re.DOTALL),
    re.compile(r"every (?:raw )?(?:record|file|job).{0,120}transpiled_qasm", re.IGNORECASE | re.DOTALL),
    re.compile(r"minden (?:fájl|rekord).{0,120}transpiled_qasm", re.IGNORECASE | re.DOTALL),
    re.compile(r"mind(?:en)?(?:,)? ?(?:a )?(?:fájl|rekord)", re.IGNORECASE | re.DOTALL),
)


def _find_value(blob: object, keys: tuple[str, ...]) -> object | None:
    """Depth-first search for any of `keys`, so nested job records are found."""
    if isinstance(blob, dict):
        for k, v in blob.items():
            if k in keys:
                return v
        for v in blob.values():
            found = _find_value(v, keys)
            if found is not None:
                return found
    elif isinstance(blob, list):
        for v in blob[:64]:  # bounded: a huge counts map adds nothing
            found = _find_value(v, keys)
            if found is not None:
                return found
    return None


def _counts_total(counts: object) -> int | None:
    """Total shots implied by a counts mapping, or None if not a mapping."""
    if isinstance(counts, dict):
        try:
            return sum(int(v) for v in counts.values() if isinstance(v, (int, float)))
        except (TypeError, ValueError):
            return None
    return None


def inspect_records() -> tuple[list[dict[str, object]], list[str]]:
    """Measure every record. Returns (summaries, hard_errors)."""
    summaries: list[dict[str, object]] = []
    hard_errors: list[str] = []

    if not RAW_DIR.is_dir():
        return summaries, [f"missing directory: {RAW_DIR.relative_to(ROOT)}"]

    files = sorted(RAW_DIR.glob("*.json"))
    if not files:
        return summaries, [f"no *.json records found under {RAW_DIR.relative_to(ROOT)}"]

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            hard_errors.append(f"{rel}: does not parse as JSON ({type(exc).__name__})")
            continue

        job_id = _find_value(blob, JOB_ID_KEYS)
        counts = _find_value(blob, COUNTS_KEYS)
        has_qasm = _find_value(blob, QASM_KEYS) is not None
        has_props = _find_value(blob, BACKEND_PROPS_KEYS) is not None

        mem_val = _find_value(blob, ("memory",))
        mem_len: int | None = None
        if isinstance(mem_val, list):
            mem_len = len(mem_val)
        elif isinstance(mem_val, str):
            mem_len = len(mem_val.split())

        summaries.append({
            "file": rel,
            "job_id": str(job_id) if job_id is not None else None,
            "counts_total": _counts_total(counts),
            "has_qasm": has_qasm,
            "has_props": has_props,
            "memory_len": mem_len,
        })

        if job_id is None:
            hard_errors.append(f"{rel}: no job identifier found")
        if counts is None:
            hard_errors.append(f"{rel}: no counts found")

    return summaries, hard_errors


def check_truncated_memory(summaries: list[dict[str, object]]) -> list[str]:
    """Report records whose stored memory is shorter than the counts total.

    Informational, not fatal: a partial memory list is evidence of an incomplete
    save, and the only correct response to that is to say so, not to hide it.
    """
    notes: list[str] = []
    for s in summaries:
        total, mem = s["counts_total"], s["memory_len"]
        if isinstance(total, int) and isinstance(mem, int) and mem < total:
            notes.append(
                f"{s['file']}: memory holds {mem} of {total} returned shots "
                f"({mem / total * 100:.1f}%) — the save was truncated"
            )
    return notes


def check_document_claims(summaries: list[dict[str, object]]) -> list[str]:
    """Fail when a published document asserts uniformity the data lacks."""
    findings: list[str] = []
    complete = [s for s in summaries if s["has_qasm"] and s["has_props"]]
    incomplete = [s for s in summaries if not (s["has_qasm"] and s["has_props"])]

    for rel in CLAIMING_DOCS:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for pattern in UNIVERSAL_CLAIM_PATTERNS:
            for match in pattern.finditer(text):
                # A claim that is immediately QUALIFIED is the corrected
                # wording and must not be flagged. The window has to cover the
                # whole match (these patterns span lines) plus the few lines
                # that follow it, because the qualification is written as a
                # caveat right below the claim it limits.
                span_start = max(0, text.rfind("\n", 0, match.start()))
                tail_end = text.find("\n", match.end())
                span_end = tail_end if tail_end != -1 else len(text)
                window = text[span_start:span_end + 400]
                qualifier = re.compile(
                    r"except|however|not\b|kivétel|azonban|⚠|IBM-fájlok", re.IGNORECASE)
                if qualifier.search(window):
                    continue
                findings.append(
                    f"{rel} [{pattern.pattern[:40]}...]: asserts every record "
                    f"carries the full audit trail, but {len(incomplete)} of "
                    f"{len(summaries)} records do not "
                    f"({', '.join(Path(str(s['file'])).name for s in incomplete[:3])})"
                )
                break  # one finding per document per rule is enough

    if complete:
        pass  # counted above for the report only
    return findings


def selftest() -> int:
    """Prove this checker FIRES on the false claim it was written to catch.

    A checker that has never been seen to fail is indistinguishable from one
    that cannot fail. This runs the same document-claim rule against three
    fixtures, entirely in memory:

      1. the original false sentence  -> MUST be flagged
      2. the corrected, qualified one  -> MUST stay silent
      3. a document with no claim at all -> MUST stay silent

    Case 2 matters as much as case 1: a checker that fires on correct
    documentation gets switched off within a week.
    """
    print("=== audit-trail checker self-test ===")

    # A stand-in for the measured state: 3 complete records, 1 incomplete.
    fake: list[dict[str, object]] = [
        {"file": "measurement_raw/a.json", "has_qasm": True, "has_props": True},
        {"file": "measurement_raw/b.json", "has_qasm": True, "has_props": True},
        {"file": "measurement_raw/c.json", "has_qasm": True, "has_props": True},
        {"file": "measurement_raw/d.json", "has_qasm": False, "has_props": False},
    ]

    original_docs = CLAIMING_DOCS
    original_root = ROOT

    def scan(text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "fixture.md").write_text(text, encoding="utf-8")
            globals()["ROOT"] = Path(td)
            globals()["CLAIMING_DOCS"] = ("fixture.md",)
            try:
                return check_document_claims(fake)
            finally:
                globals()["ROOT"] = original_root
                globals()["CLAIMING_DOCS"] = original_docs

    false_text = (
        "# Ledger\n"
        "All raw data in `measurement_raw/` with job IDs, counts, backend "
        "properties, transpiled QASM.\n"
    )
    corrected_text = (
        "# Ledger\n"
        "All raw data in `measurement_raw/` with job IDs and counts. The IBM "
        "records also carry backend properties and the transpiled circuit.\n"
        "\n"
        "Except the IQM record: it has neither.\n"
    )
    silent_text = "# Ledger\n\nNo audit-trail claim is made here.\n"

    failures = 0

    fired = scan(false_text)
    if fired:
        print("  OK   flags the original false claim")
    else:
        print("  FAIL did NOT flag the false claim — this checker cannot fail")
        failures += 1

    quiet = scan(corrected_text)
    if not quiet:
        print("  OK   silent on the qualified/corrected wording")
    else:
        print(f"  FAIL false positive on corrected text: {quiet[0]}")
        failures += 1

    quiet2 = scan(silent_text)
    if not quiet2:
        print("  OK   silent on a document with no such claim")
    else:
        print(f"  FAIL false positive on unrelated text: {quiet2[0]}")
        failures += 1

    print()
    if failures:
        print(f"RESULT: FAIL ({failures} problem(s))")
        return 1
    print("RESULT: PASS — checker fires on the defect and respects the fix")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    print("=" * 74)
    print("QUANTUM ANCHOR — AUDIT TRAIL COMPLETENESS (measured, not asserted)")
    print("=" * 74)
    print()

    summaries, hard_errors = inspect_records()

    if not summaries:
        print("[FAIL] no records could be measured")
        for err in hard_errors:
            print(f"  ! {err}")
        return 1

    with_qasm = sum(1 for s in summaries if s["has_qasm"])
    with_props = sum(1 for s in summaries if s["has_props"])
    with_job = sum(1 for s in summaries if s["job_id"])
    with_counts = sum(1 for s in summaries if isinstance(s["counts_total"], int))

    print(f"records measured      : {len(summaries)}")
    print(f"  with job_id         : {with_job}/{len(summaries)}")
    print(f"  with counts         : {with_counts}/{len(summaries)}")
    print(f"  with transpiled_qasm: {with_qasm}/{len(summaries)}")
    print(f"  with backend_props  : {with_props}/{len(summaries)}")
    print()

    incomplete = [s for s in summaries
                  if not (s["has_qasm"] and s["has_props"])]
    if incomplete:
        print("incomplete records (job ID + counts only):")
        for s in incomplete:
            print(f"  - {Path(str(s['file'])).name}")
        print()

    notes = check_truncated_memory(summaries)
    if notes:
        print("truncated memory (informational, see VALIDATION.md):")
        for note in notes:
            print(f"  - {note}")
        print()

    doc_findings = check_document_claims(summaries)
    findings = hard_errors + doc_findings

    print("=" * 74)
    if findings:
        print(f"FINDINGS ({len(findings)})")
        print("=" * 74)
        for f in findings:
            print(f"  ! {f}")
        print()
        print("RESULT: FAIL — the published audit trail does not match the files.")
        return 1

    print("RESULT: PASS — every published audit-trail claim matches the files")
    if incomplete:
        print(f"        ({len(incomplete)} incomplete record(s), documented as such)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
