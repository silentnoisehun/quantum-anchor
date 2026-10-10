#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verzio-drift ellenorzo. Exit 1 ha drift -> pre-commit hook.

python version_drift.py [repo]      (default: a sajat munkakonyvtar)
A CITATION.cff, .zenodo.json, README, white paper, arXiv tex es git tag
altal deklaralt verziot osszeveti.
"""
import json, os, re, subprocess, sys

R = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '.'
R = os.path.abspath(R)
V = r'(\d+\.\d+\.\d+)'
SRC = []


def rd(p):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except OSError:
        return None


def add(label, version, path):
    SRC.append((label, version, path))


for label, path, pat in (
        ('CITATION.cff', 'CITATION.cff', r'^version:\s' + V),
        ('README.md', 'README.md', 'Quantum Anchor V' + V),
        ('whitepaper', None, 'Quantum Anchor V' + V),
        ('arxiv tex', None, 'Quantum Anchor V' + V)):
    if path is None:
        continue
    m = re.search(pat, rd(os.path.join(R, path)) or '', re.M)
    add(label, m.group(1) if m else None, path)

t = rd(os.path.join(R, '.zenodo.json'))
try:
    add('.zenodo.json', json.loads(t)['version'] if t else None, '.zenodo.json')
except Exception:
    add('.zenodo.json', None, '.zenodo.json')

for folder, stem in (('docs', 'HOPE-WP-'), ('arxiv', '')):
    d = os.path.join(R, folder)
    if not os.path.isdir(d):
        continue
    for name in sorted(os.listdir(d)):
        if not name.endswith(('.md', '.tex')):
            continue
        if folder == 'docs' and not name.startswith(stem):
            continue
        t = rd(os.path.join(d, name)) or ''
        m = re.search('Quantum Anchor V' + V, t)
        add(folder, m.group(1) if m else None, folder + '/' + name)
        f = re.search(r'[Vv](\d+(?:\.\d+)*)', name)
        if f:
            add(folder + ' fname', f.group(1), folder + '/' + name)

try:
    tags = subprocess.run(['git', 'tag', '-l', 'v*.*.*'], cwd=R,
                          capture_output=True, text=True, timeout=15).stdout
    tags = sorted([x.strip().lstrip('v') for x in tags.split() if x.strip()],
                  key=lambda s: [int(p) for p in s.split('.')])
    tag = tags[-1] if tags else None
except Exception:
    tag = None

DECL = sorted({v for l, v, p in SRC if v and not l.endswith('fname')})
print('Verzio-drift: ' + R)
for l, v, p in SRC:
    print('  %-14s %-10s %s' % (l, v or '?', p))

PROB = []
miss = [l for l, v, p in SRC if not v and not l.endswith('fname')]
if miss:
    PROB.append('nem kiolvashato: ' + ', '.join(miss))
if len(DECL) > 1:
    PROB.append('eltéro verziok: ' + ', '.join(DECL))
if DECL:
    stem = '.'.join(DECL[-1].split('.')[:2])
    for l, v, p in SRC:
        if v and l.endswith('fname') and not v.startswith(stem):
            PROB.append('fajlnev lemaradt: %s (%s, tartalom %s)'
                        % (p, v, DECL[-1]))
    if tag and tag not in DECL:
        PROB.append('a legutolbi git tag (%s) nincs a deklaraltak kozott '
                    '- ha kiadott, a deklalacio lemaradt' % tag)
    elif tag != DECL[-1]:
        PROB.append('deklaralt %s, de legutolbi tag %s' % (DECL[-1], tag))

print('')
if PROB:
    print('DRIFT TALALT:')
    for x in PROB:
        print('  - ' + x)
    print('javitas vagy --no-verify')
    sys.exit(1)
print('Rendben: ' + DECL[0] + (', tag ' + tag if tag else ''))
