#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drive_survey.py -- meghajto- es mappat Inventory, olvasasi modszerben.

Nincs semmit torol vagy mozgat. Csak mer.

    python drive_survey.py <cel> [--top N] [--min-mb N] [--mindepth N]

Peldul:
    python drive_survey.py D: --top 25
    python drive_survey.py "D:/projektek" --min-mb 100
"""
import os
import sys
import time


def dir_size(path, max_depth=99):
    total = 0
    files = 0
    stack = [(path, 0)]
    errors = 0
    while stack:
        cur, depth = stack.pop()
        try:
            with os.scandir(cur) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if depth < max_depth:
                                stack.append((e.path, depth + 1))
                        elif e.is_file(follow_symlinks=False):
                            total += e.stat(follow_symlinks=False).st_size
                            files += 1
                    except OSError:
                        errors += 1
        except OSError:
            errors += 1
    return total, files, errors


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024 or unit == 'TB':
            return '%.1f %s' % (n, unit)
        n /= 1024.0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    top = 25
    min_mb = 5.0
    for a in sys.argv:
        if a.startswith('--top'):
            top = int(a.split('=')[1]) if '=' in a else top
        if a.startswith('--min-mb'):
            min_mb = float(a.split('=')[1]) if '=' in a else min_mb

    target = args[0] if args else '.'
    target = os.path.abspath(target)
    print('CEL: %s' % target)
    print('=' * 74)

    rows = []
    t0 = time.time()
    try:
        entries = sorted(os.scandir(target), key=lambda e: e.name.lower())
    except OSError as exc:
        print('Nem lehet olvasni: %s' % exc)
        return 2

    for e in entries:
        try:
            if not e.is_dir(follow_symlinks=False):
                continue
        except OSError:
            continue
        sz, n, err = dir_size(e.path)
        rows.append((sz, n, err, e.path))

    rows.sort(reverse=True)
    print('%-11s %9s %7s  %s' % ('meret', 'fajlok', 'hibak', 'utvonal'))
    print('-' * 74)
    shown = 0
    for sz, n, err, p in rows:
        if sz < min_mb * 1024 * 1024:
            continue
        print('%-11s %9d %7d  %s' % (human(sz), n, err, p))
        shown += 1
        if shown >= top:
            break

    grand = sum(r[0] for r in rows)
    small = len([r for r in rows if r[0] < min_mb * 1024 * 1024])
    print('-' * 74)
    print('osszesen %d mappa | osszzesen %s | %d mappa %.0f MB alatt'
          % (len(rows), human(grand), small, min_mb))
    print('ido: %.1f mp' % ((time.time() - t0) / 60.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
