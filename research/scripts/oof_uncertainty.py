"""Conditional event-cluster uncertainty for frozen development predictions."""
import argparse
import json
from pathlib import Path

import numpy as np

from hybrid_cv import digest


def resample(correct, groups, draws=5000, seed=20261004):
    correct=np.asarray(correct,dtype=float)
    if correct.ndim!=2 or correct.shape[1]==0 or correct.shape[0]!=len(groups) or not len(groups) or not np.isin(correct,[0,1]).all():
        raise ValueError('Expected aligned nonempty binary correctness matrix')
    if any(not isinstance(group,str) or not group.strip() for group in groups):
        raise ValueError('Nonblank event-string groups required')
    if type(draws) is not int or draws<1:raise ValueError('Positive integer draw count required')
    names=sorted(set(groups))
    sizes=np.array([sum(g==name for g in groups) for name in names])
    sums=np.array([correct[np.array(groups)==name].sum(axis=0) for name in names])
    rng=np.random.default_rng(seed)
    counts=rng.multinomial(len(names),np.full(len(names),1/len(names)),size=draws)
    estimates=(counts@sums)/(counts@sizes)[:,None]
    return estimates,counts,names


def run(data, source, output):
    if output.exists():raise ValueError('Use a new output directory')
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    prior=json.loads(source.read_text())
    if prior['inputs'].get(str(data))!=digest(data):raise ValueError('Data hash mismatch')
    byid={r['id']:r for r in prior['records']}
    if len(byid)!=len(prior['records']) or len(rows)!=len(byid) or {r['id'] for r in rows}!=set(byid):
        raise ValueError('Reference/prediction IDs differ')
    models=prior['models']
    if len(set(models))!=len(models) or 'word' not in models:raise ValueError('Invalid model names')
    for row in rows:
        record=byid[row['id']]
        if row['label']!=record['reference_label'] or row['text_sha256']!=record['text_sha256'] or set(record['predictions'])!=set(models):
            raise ValueError('Reference or model alignment changed')
    correct=np.array([[byid[r['id']]['predictions'][m]==r['label'] for m in models] for r in rows])
    estimates,counts,groups=resample(correct,[r['event'] for r in rows])
    baseline=models.index('word')
    differences=estimates-estimates[:,baseline,None]
    output.mkdir(parents=True)
    replicates=output/'replicates.npz'
    np.savez_compressed(replicates,group_draw_counts=counts,accuracy=estimates,paired_differences=differences)
    report=dict(purpose='Conditional uncertainty of fixed training OOF predictions, not independent accuracy',
        validation_read=False,reserved_test_read=False,retraining=False,release_approved=False,
        source_sha256=digest(source),data_sha256=digest(data),replicates_sha256=digest(replicates),
        settings=dict(draws=5000,seed=20261004,method='Event-string cluster percentile bootstrap',
                      weighting='Uniform cluster draws; all rows per selected group; sample-weighted accuracy'),
        numpy_version=np.__version__,group_order=groups,model_order=models,
        row_ids=[r['id'] for r in rows],row_groups=[r['event'] for r in rows],results={},
        limitations=['Conditions on saved predictions; excludes retraining variability',
            'Overlapping training folds induce dependence not resolved by this bootstrap',
            'Event-string groups are not proven independent event families',
            'Repeatedly explored development data and multiple comparisons; no significance claims',
            'Disputed noncommercial corpus labels; not product evaluation'])
    points=correct.mean(axis=0)
    for i,name in enumerate(models):
        report['results'][name]=dict(accuracy=float(points[i]),
            accuracy_percentile_95=np.quantile(estimates[:,i],[.025,.975]).tolist(),
            paired_delta=float(points[i]-points[baseline]),
            paired_delta_percentile_95=np.quantile(differences[:,i],[.025,.975]).tolist())
    (output/'results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report['results'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('data','source','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.data,a.source,a.output)
