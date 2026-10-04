"""Fixed CENTER-first hard-gated classifier; training-only development CV."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression

from corpus_experiment import metrics
from hybrid_cv import digest, validate_split


def combine(center, conditional):
    if not 0 <= center <= 1 or set(conditional) != {'LEFT', 'RIGHT'}:
        raise ValueError('Invalid probabilities')
    if any(not 0 <= p <= 1 for p in conditional.values()) or not np.isclose(sum(conditional.values()), 1):
        raise ValueError('Invalid conditional distribution')
    scores = {'CENTER': center, **{k: (1-center)*v for k,v in conditional.items()}}
    label = 'CENTER' if center >= .5 else max(conditional, key=conditional.get)
    return label, scores


def run(data, folds, output):
    if output.exists():
        raise ValueError('Use a new output directory')
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    prior = json.loads((folds/'training_results.json').read_text())
    if prior['input_sha256'] != digest(data):
        raise ValueError('Input hash mismatch')
    lookup = {r['id']:r for r in rows}
    settings = dict(C=1, class_weight='balanced', solver='lbfgs', max_iter=1000, random_state=20261001)
    record = dict(purpose='Exploratory training-only grouped CV, not independent accuracy',
        validation_read=False, reserved_test_read=False, release_approved=False,
        data_sha256=digest(data), fold_manifest_sha256=digest(folds/'training_results.json'),
        settings=settings, gate=.5, decision_rule='CENTER if p>=.5 else conditional LEFT/RIGHT argmax',
        sklearn_version=sklearn.__version__, folds=[], oof={'word':[], 'hierarchy':[]})
    output.mkdir(parents=True)
    (output/'protocol.json').write_text(json.dumps(record,indent=2))
    for split in prior['folds']:
        train, held = split['train_ids'],split['held_ids']
        validate_split(rows,train,held)
        path = folds/f"fold-{split['fold']}-baseline.joblib"
        if digest(path) != split['models']['baseline']['model_sha256']:
            raise ValueError('Baseline hash mismatch')
        saved = joblib.load(path)
        vec = saved['vectorizer']
        x = vec.transform([lookup[i]['text'] for i in train])
        h = vec.transform([lookup[i]['text'] for i in held])
        labels = np.array([lookup[i]['label'] for i in train])
        center = LogisticRegression(**settings).fit(x,labels=='CENTER')
        partisan = labels!='CENTER'
        direction = LogisticRegression(**settings).fit(x[partisan],labels[partisan])
        dest = output/f"fold-{split['fold']}.joblib"
        joblib.dump(dict(vectorizer=vec,center=center,direction=direction,gate=.5),dest)
        cp = center.predict_proba(h)[:,list(center.classes_).index(True)]
        dp = direction.predict_proba(h)
        wp = saved['classifier'].predict_proba(h)
        for n,id in enumerate(held):
            conditional = dict(zip(direction.classes_.tolist(),dp[n].tolist()))
            prediction,scores = combine(float(cp[n]),conditional)
            record['oof']['hierarchy'].append(dict(id=id,fold=split['fold'],prediction=prediction,
                probabilities=scores,center_score=float(cp[n]),conditional_scores=conditional))
            record['oof']['word'].append(dict(id=id,fold=split['fold'],prediction=str(saved['classifier'].classes_[wp[n].argmax()]),
                probabilities=dict(zip(saved['classifier'].classes_.tolist(),wp[n].tolist()))))
        record['folds'].append(dict(fold=split['fold'],train_ids=train,held_ids=held,
            baseline_sha256=digest(path),model_sha256=digest(dest),partisan_training_n=int(partisan.sum()),
            center_iterations=center.n_iter_.tolist(),direction_iterations=direction.n_iter_.tolist()))
        (output/'training_results.json').write_text(json.dumps(record,indent=2))
        print('completed',split['fold'],flush=True)
    record['metrics']={}
    for name,predictions in record['oof'].items():
        byid = {p['id']:p['prediction'] for p in predictions}
        if len(predictions)!=len(rows) or set(byid)!=set(lookup):
            raise ValueError('Incomplete OOF coverage')
        record['metrics'][name]=metrics(rows,[byid[r['id']] for r in rows])
    (output/'training_results.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record['metrics'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('data','folds','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    run(a.data,a.folds,a.output)
