"""Verify that the Quantum Anchor model depends on the standard library ONLY.

Run: python -m src.check_no_dependencies

WHY THIS EXISTS
---------------
The ledger in docs/VALIDATION.md claims the project needs no third-party
package. This script makes that claim falsifiable instead of decorative. It
parses this project's own source files with the standard-library `ast` module
and lists every top-level module they import, so a reviewer does not have to
take the README on faith.

The check is deliberately static. Measuring `sys.modules` after import is
useless here: the interpreter preloads whatever the platform bootstrapped
(pywin32_* on Windows, for instance), which has nothing to do with this
project. Reading the import statements from the source is the only method
that answers the actual question.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Modules that are part of the standard library.
STDLIB = set(sys.stdlib_module_names)

# The project's own top-level packages, which are obviously not stdlib.
OWN_PACKAGES = {"src"}


def imports_of(path: Path) -> set[str]:
    """Return every top-level module name imported by one source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # `from .x import y` has no module; level > 0 means relative.
            if node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


def main() -> int:
    src_dir = Path(__file__).resolve().parent
    sources = sorted(src_dir.glob("*.py"))
    if not sources:
        print("no sources found — refusing to pass vacuously")
        return 1

    # This file must not police itself, or it would always flag its own name.
    self_name = Path(__file__).stem

    all_imports: dict[str, set[str]] = {}
    for source in sources:
        if source.stem == self_name:
            continue
        all_imports[source.name] = imports_of(source)

    offenders: dict[str, set[str]] = {}
    for name, mods in all_imports.items():
        external = {
            m for m in mods
            if m not in STDLIB and m not in OWN_PACKAGES
        }
        if external:
            offenders[name] = external

    print("Quantum Anchor — dependency audit")
    print("=" * 55)
    for name, mods in sorted(all_imports.items()):
        external = sorted(m for m in mods if m not in STDLIB and m not in OWN_PACKAGES)
        status = "OK" if not external else f"THIRD-PARTY: {external}"
        print(f"  {name:<22} -> {sorted(mods)}")
        if external:
            print(f"  {'':<22}    {status}")
    print()

    if offenders:
        print("FAIL: the project imports third-party packages:")
        for name, external in offenders.items():
            print(f"  {name}: {sorted(external)}")
        print()
        print("The ledger in docs/VALIDATION.md states the project needs no")
        print("third-party dependency. Either that is wrong, or this file")
        print("imports something it should not.")
        return 1

    print(f"PASS: {len(all_imports)} source file(s) import the standard library only.")
    print("This is a STATIC check of the project's own imports. It says")
    print("nothing about hardware — no QPU was involved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
