#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kar-fix -- egyedi kar javitasa/torlese a wave-echo spine-ban.

A `hullam add-native` append-only, nincs torlo vagy frissito parancsa, ezert
ez a tool maga szerkeszti a spine slotot. A spine 2048 fix, 4048 bajtos slotot
tartalmaz (8290304 B), ezert az in-place iras fizikailag biztonsagos.

    python kar_fix.py <spine.rgs> list
    python kar_fix.py <spine.rgs> locate  <needle>
    python kar_fix.py <spine.rgs> disable <needle> [--yes]
    python kar_fix.py <spine.rgs> replace <needle> <fajl> [--yes]

BIZTONSAGI SZABALY: a spine-ben nincs megbizhataho ID -> slot terkep
(merest: slot-minus-ID +3..+7, nem konzisztens), ezert a tool NEM kar-ID
segitsagvel keres, hanem a hivaso altal adott egyedi markerre (needle).
Minden iras elott elonezetet nyomtat, es --yes nelkul nem ir semmit.
Ha a marker nem egyertelmuen egyetlen sloton van, NEM MODOSIT.
"""
import os
import shutil
import struct
import sys

SLOT = 4048
HULLAM = r'D:\codex\octopus-agent-kit\bin\hullam.exe'
TOMB = b'KAR_DISABLED_BY_KAR_FIX'


def load(path):
    data = open(path, 'rb').read()
    return data, len(data) // SLOT


def all_slots(data, needle):
    b = needle.encode()
    out = []
    if not b or len(b) > SLOT:
        return out
    for s in range(len(data) // SLOT):
        i = data.find(b, s * SLOT, (s + 1) * SLOT)
        if i >= 0:
            out.append((s, i - s * SLOT))
    return out


def preview(path, slot):
    data, n = load(path)
    raw = data[slot * SLOT:(slot + 1) * SLOT]
    txt = raw.decode('utf-8', 'replace')
    clean = ''.join(c if (c.isprintable() or c == '\n') else '.' for c in txt)
    return clean.strip()[:300]


def resolve(data, needle, action):
    hits = all_slots(data, needle)
    if not hits:
        print('NEM MODOSITOK: a marker egyik sloton sincs: %r' % needle)
        return None
    if len(hits) > 1:
        print('NEM MODOSITOK: a marker %d sloton is megvan (%s). '
              'Nem talalgatok -- adj szukebb markert.'
              % (len(hits), [h[0] for h in hits]))
        return None
    return hits[0][0]


def confirm(path, slot, needle, action, yes):
    print('--- ELOZNEZES (slot %d) ---' % slot)
    print(preview(path, slot))
    print('--- MUVELET: %s | marker: %r ---' % (action, needle))
    if not yes:
        print('NEM MODOSITOK. Ha ez a kart akarod, add --yes-t a parancshoz.')
        return False
    return True


def backup(path):
    bak = path + '.karfix.bak'
    shutil.copy2(path, bak)
    return bak


def write_slot(path, slot, payload):
    with open(path, 'r+b') as fh:
        fh.seek(slot * SLOT)
        fh.write(struct.pack('<I', len(payload)))
        fh.write(payload)
        fh.write(b'\x00' * (SLOT - 4 - len(payload)))


def cmd_list(path):
    data, n = load(path)
    used = sum(1 for s in range(n)
               if data[s * SLOT:(s + 1) * SLOT].strip(b'\x00'))
    print('spine : %s' % path)
    print('  meret %d B | slot %d B | slotok %d | nem ures %d | kar-limit %d B'
          % (len(data), SLOT, n, used, SLOT))
    return 0


def cmd_locate(path, needle):
    data, n = load(path)
    hits = all_slots(data, needle)
    if not hits:
        print('Nincs talalat.')
        return 2
    for s, off in hits:
        print('slot %-6d offset %d' % (s, off))
    return 0 if len(hits) == 1 else 1


def cmd_disable(path, needle, yes):
    data, n = load(path)
    slot = resolve(data, needle, 'DISABLE')
    if slot is None:
        return 2
    if not confirm(path, slot, needle, 'DISABLE', yes):
        return 2
    bak = backup(path)
    write_slot(path, slot, TOMB)
    print('TORLOVE: slot %d tombstone-t tartalmaz. backup: %s' % (slot, bak))
    return 0


def cmd_replace(path, needle, src, yes):
    data, n = load(path)
    slot = resolve(data, needle, 'REPLACE')
    if slot is None:
        return 2
    new = open(src, 'rb').read()
    if len(new) > SLOT - 4:
        print('NEM MODOSITOK: %d B > slot %d B.' % (len(new), SLOT))
        return 2
    if not confirm(path, slot, needle, 'REPLACE', yes):
        return 2
    bak = backup(path)
    write_slot(path, slot, new)
    print('FRISSITVE: slot %d, uj tartalom %d B. backup: %s'
          % (slot, len(new), bak))
    return 0


def main():
    if len(sys.argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    path, cmd = sys.argv[1], sys.argv[2]
    yes = '--yes' in sys.argv
    if not os.path.exists(path):
        print('Nincs fajl: ' + path)
        return 2
    if cmd == 'list':
        return cmd_list(path)
    if cmd == 'locate' and len(sys.argv) >= 4:
        return cmd_locate(path, sys.argv[3])
    if cmd == 'disable' and len(sys.argv) >= 4:
        return cmd_disable(path, sys.argv[3], yes)
    if cmd == 'replace' and len(sys.argv) >= 5:
        return cmd_replace(path, sys.argv[3], sys.argv[4], yes)
    sys.stderr.write(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
