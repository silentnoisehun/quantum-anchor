#!/usr/bin/env python3
"""Save phase 0 audit for IQM job 01a11943-739b-7415-8719-1fa493bc9aa8"""

import os
import json
from datetime import datetime
from iqm.qiskit_iqm import IQMProvider

def main():
    token = os.getenv("IQM_TOKEN")
    if not token:
        print("[HIBA] IQM_TOKEN környezeti változó nincs beállítva.")
        return 1
    
    provider = IQMProvider('https://resonance.iqm.tech', quantum_computer='garnet')
    backend = provider.get_backend()
    job_id = '01a11943-739b-7415-8719-1fa493bc9aa8'
    job = backend.retrieve_job(job_id)
    result = job.result()
    counts = dict(result.get_counts())
    returned = sum(counts.values())
    c0 = counts.get('00000000', 0)
    c1 = counts.get('11111111', 0)
    global_coherence = (c0 + c1) / returned * 100.0

    audit = {
        'job_id': job_id,
        'backend': 'garnet',
        'num_qubits': 20,
        'status': 'DONE',
        'shots': returned,
        'counts': counts,
        'global_coherence_pct': global_coherence,
        'c0': c0,
        'c1': c1,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f'measurement_raw/iqm_anchor_{job_id}_phase0_audit_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(audit, f, indent=2)

    print(f'Audit saved: {filename}')
    print(f'Global coherence: {global_coherence:.2f}% (0^8={c0}, 1^8={c1})')
    return 0

if __name__ == '__main__':
    exit(main())