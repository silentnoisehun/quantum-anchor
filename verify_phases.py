import json
import math
from pathlib import Path

def wilson_ci95(successes, trials):
    if trials <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return [round(max(0.0, center - margin) * 100.0, 3), round(min(1.0, center + margin) * 100.0, 3)]

raw_dir = Path(r'C:\Users\mater\Documents\orassh\quantum_anchor\measurement_raw')

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

phase0 = load_json(raw_dir / 'phase0_audit_latest.json')
c0_0 = phase0.get('c0', phase0['counts'].get('00000000', 0))
c1_0 = phase0.get('c1', phase0['counts'].get('11111111', 0))
print('Phase 0: c0={}, c1={}, job_id={}'.format(c0_0, c1_0, phase0["job_id"]))

phase1 = load_json(raw_dir / 'iqm_tesseract_v3_interferometric_01a11ab7_phase1_20261008T085544Z.json')
c0_1 = phase1['counts'].get('00000000', 0)
c1_1 = phase1['counts'].get('11111111', 0)
print('Phase 1: c0={}, c1={}, job_id={}'.format(c0_1, c1_1, phase1["job_id"]))

phase2 = load_json(raw_dir / 'iqm_tesseract_v3_interferometric_01a11aba_phase2_20261008T085622Z.json')
c0_2 = phase2['counts'].get('00000000', 0)
c1_2 = phase2['counts'].get('11111111', 0)
print('Phase 2: c0={}, c1={}, job_id={}'.format(c0_2, c1_2, phase2["job_id"]))

phase3 = load_json(raw_dir / 'iqm_tesseract_v3_interferometric_01a11aba_phase3_20261008T085652Z.json')
c0_3 = phase3['counts'].get('00000000', 0)
c1_3 = phase3['counts'].get('11111111', 0)
print('Phase 3: c0={}, c1={}, job_id={}'.format(c0_3, c1_3, phase3["job_id"]))

phase4 = load_json(raw_dir / 'iqm_tesseract_v3_interferometric_01a11abb_phase4_20261008T085727Z.json')
c0_4 = phase4['counts'].get('00000000', 0)
c1_4 = phase4['counts'].get('11111111', 0)
print('Phase 4: c0={}, c1={}, job_id={}'.format(c0_4, c1_4, phase4["job_id"]))