#!/usr/bin/env python3
"""Save audit JSON for IQM phases 1-4"""

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

    job_ids = [
        ('01a11ab7-7d8e-77c3-bc67-ae8423181204', 1),  # phase 1
        ('01a11aba-531f-73ae-8da7-c705c729038d', 2),  # phase 2
        ('01a11aba-c6d7-736a-ac56-a5c0525d2cc4', 3),  # phase 3
        ('01a11abb-525f-7534-a1f1-5c98b274d710', 4),  # phase 4
    ]

    for job_id, phase_idx in job_ids:
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
            'phase': phase_idx,
            'status': 'DONE',
            'shots_returned': returned,
            'counts': counts,
            'global_coherence_pct': round(global_coherence, 2),
            'c0': c0,
            'c1': c1,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f'measurement_raw/iqm_anchor_{job_id}_phase{phase_idx}_audit_{timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(audit, f, indent=2)
        print(f'Saved: {filename}')
        print(f'  Phase {phase_idx}: coherence={global_coherence:.2f}% (0^8={c0}, 1^8={c1})')
    
    return 0

if __name__ == '__main__':
    exit(main())