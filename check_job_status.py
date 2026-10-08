#!/usr/bin/env python3
"""Check IQM job status for job 01a11943-739b-7415-8719-1fa493bc9aa8

Token MUST come from IQM_TOKEN environment variable — never hardcode.
"""

import os
import sys

if not os.getenv("IQM_TOKEN"):
    print("[HIBA] IQM_TOKEN környezeti változó nincs beállítva.")
    print("   A token soha ne menjen CLI argumentumként vagy fájlba.")
    print(r"   PowerShell:  \$env:IQM_TOKEN = '...'")
    sys.exit(1)

try:
    from iqm.qiskit_iqm import IQMProvider
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

try:
    provider = IQMProvider('https://resonance.iqm.tech', quantum_computer='garnet')
    backend = provider.get_backend()
    print(f"Backend: {backend.name} ({backend.num_qubits} qubits)")
    
    # Try to get job status
    job_id = '01a11943-739b-7415-8719-1fa493bc9aa8'
    job = backend.retrieve_job(job_id)
    status = job.status()
    print(f"Job ID: {job_id}")
    print(f"Status: {status}")
    
    status_str = str(status).upper()
    if 'DONE' in status_str or 'COMPLETED' in status_str or 'SUCCESS' in status_str:
        result = job.result()
        counts = dict(result.get_counts())
        returned = sum(counts.values())
        c0 = counts.get("00000000", 0)
        c1 = counts.get("11111111", 0)
        global_coherence = (c0 + c1) / returned * 100.0
        print(f"Shots returned: {returned}")
        print(f"Global coherence: {global_coherence:.2f}% (0^8={c0}, 1^8={c1})")
        print(f"Top counts: {sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]}")
    else:
        print("Job still in queue/running")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()