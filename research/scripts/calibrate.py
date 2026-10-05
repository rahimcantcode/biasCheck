"""Fit only on validation; never marks a policy as approved for deployment."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp,softmax
try:
    from .report_contract import require_human_provenance, require_unique_examples, require_numeric_predictions
except ImportError:
    from report_contract import require_human_provenance, require_unique_examples, require_numeric_predictions


def fit(report,target=.9,min_coverage=.8):
    if report['split']!='validation':raise ValueError('Only validation may be used for calibration.')
    require_human_provenance(report)
    require_unique_examples(report)
    require_numeric_predictions(report)
    rows=[r for r in report['predictions'] if r['gold'] in ['LEFT','CENTER','RIGHT']]
    if len(rows)<100:raise ValueError('At least 100 validation examples are required.')
    mapping={v:int(k) for k,v in report['model']['id2label'].items()}
    y=np.array([mapping[r['gold']] for r in rows]);logits=np.array([r['logits'] for r in rows])
    def nll(log_t):
        z=logits/np.exp(log_t)
        return np.mean(logsumexp(z,axis=1)-z[np.arange(len(y)),y])
    optimized=minimize_scalar(nll,bounds=(-3,3),method='bounded')
    if not optimized.success or not np.isfinite(optimized.x) or not -3 <= optimized.x <= 3 or not np.isfinite(optimized.fun):
        raise ValueError('Temperature optimization failed or returned an invalid result. Do not release.')
    temperature=float(np.exp(optimized.x))
    scores=softmax(logits/temperature,axis=1)
    if scores.shape!=logits.shape or not np.isfinite(scores).all() or (scores<0).any() or (scores>1).any() or not np.allclose(scores.sum(axis=1),1,atol=1e-10,rtol=0):
        raise ValueError('Invalid calibrated probabilities. Do not release.')
    rank=np.sort(scores,axis=1);correct=scores.argmax(1)==y
    token_counts=np.array([r['token_count'] for r in rows]);best=None
    for threshold in np.linspace(1/3,.99,80):
        for margin in np.linspace(0,.8,41):
            mask=(rank[:,-1]>=threshold)&(rank[:,-1]-rank[:,-2]>=margin)&(token_counts>=30)
            coverage=float(mask.mean());accuracy=float(correct[mask].mean()) if mask.any() else 0
            if coverage>=min_coverage and accuracy>=target and (best is None or coverage>best[0]):best=(coverage,float(threshold),float(margin),accuracy)
    if best is None:raise ValueError('Validation does not meet requested accuracy/coverage. Do not release.')
    policy={k:report['model'][k] for k in ['weights_sha256','config_sha256','tokenizer_sha256','aggregation','max_length','stride']}
    policy.update(schema_version=1,temperature=temperature,min_confidence=best[1],min_margin=best[2],min_tokens=30,
        validated_modes=[report['mode']],calibration_data_sha256=report['data_sha256'],validation_coverage=best[0],
        validation_selective_accuracy=best[3],release_approved=False,
        limitations='Requires independent test and relevance evaluation. Minimum context is an engineering guard, not a nonpolitical classifier.')
    return policy

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validation',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    policy=fit(json.loads(a.validation.read_text()));policy['validation_report_sha256']=hashlib.sha256(a.validation.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(policy,indent=2));print('Unapproved candidate policy written.')
