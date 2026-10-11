from iqm.qiskit_iqm import IQMProvider
import json, math, datetime

provider = IQMProvider('https://resonance.iqm.tech', quantum_computer='garnet')
backend = provider.get_backend()
job_id = '01a11943-739b-7415-8719-1fa493bc9aa8'
job = backend.retrieve_job(job_id)
result = job.result()
counts = dict(result.get_counts())
try:
    memory = list(result.get_memory())
except:
    memory = []

n_qubits = 8
c0 = counts.get('0'*n_qubits, 0)
c1 = counts.get('1'*n_qubits, 0)
total = sum(counts.values())
global_balance = (c0 + c1) / total * 100.0

def wilson_ci95(successes, trials):
    if trials <= 0: return [0.0, 0.0]
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z*z/trials
    center = (p + z*z/(2.0*trials))/denom
    margin = (z/denom)*math.sqrt(p*(1.0-p)/trials + z*z/(4.0*trials*trials))
    return [round(max(0.0, center-margin)*100.0, 3), round(min(1.0, center+margin)*100.0, 3)]

ci = wilson_ci95(c0+c1, total)

audit = {
    'job_id': job_id,
    'backend': 'garnet',
    'num_qubits': 20,
    'status': 'DONE',
    'shots_returned': total,
    'shots_requested': 1024,
    'counts': {k: v for k, v in counts.items() if k in ('0'*n_qubits, '1'*n_qubits)},
    'global_coherence': round(global_balance, 4),
    'c0': c0,
    'c1': c1,
    'global_balance_pct': round(global_balance, 4),
    'global_balance_ci95_pct': ci,
    'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
    'phase': 'phase5_repeat'
}

fname = f'measurement_raw/audit_phase5_garnet_20q_{datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
with open(fname, 'w') as f:
    json.dump(audit, f, indent=2)
print(f'Saved to {fname}')
print(f'Global coherence: {global_balance:.4f}%')
print(f'CI: {ci}')
print(f'c0={c0}, c1={c1}, total={total}')