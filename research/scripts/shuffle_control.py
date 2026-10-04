"""Fold-training label-shuffle controls, not an inferential permutation test."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from corpus_experiment import metrics
from hybrid_cv import digest, validate_split


def run(data, folds, output):
    if output.exists():raise ValueError('Use a new output directory')
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    prior=json.loads((folds/'training_results.json').read_text())
    if digest(data)!=prior['input_sha256']:raise ValueError('Training data mismatch')
    lookup={r['id']:r for r in rows}
    seeds=list(range(20261004,20261009))
    record=dict(purpose='Corrupted-training-label control; not an inferential permutation test',
        validation_read=False,reserved_test_read=False,release_approved=False,
        data_sha256=digest(data),fold_manifest_sha256=digest(folds/'training_results.json'),
        settings=dict(seeds=seeds,C=1,class_weight='balanced',max_iter=1000,random_state=20261001),
        runtime=dict(numpy=np.__version__,sklearn=sklearn.__version__),runs=[])
    output.mkdir(parents=True)
    (output/'protocol.json').write_text(json.dumps(record,indent=2))
    for seed in seeds:
        run=dict(seed=seed,folds=[],predictions=[])
        for split in prior['folds']:
            train,held=split['train_ids'],split['held_ids']
            validate_split(rows,train,held)
            path=folds/f"fold-{split['fold']}-baseline.joblib"
            if digest(path)!=split['models']['baseline']['model_sha256']:raise ValueError('Baseline mismatch')
            saved=joblib.load(path);vec=saved['vectorizer']
            rng=np.random.default_rng(np.random.SeedSequence([seed,split['fold']]))
            permutation=rng.permutation(len(train))
            original=[lookup[id]['label'] for id in train]
            shuffled=[original[i] for i in permutation]
            if sorted(shuffled)!=sorted(original):raise ValueError('Class count changed')
            model=LogisticRegression(C=1,class_weight='balanced',max_iter=1000,random_state=20261001)
            model.fit(vec.transform([lookup[id]['text'] for id in train]),shuffled)
            probabilities=model.predict_proba(vec.transform([lookup[id]['text'] for id in held]))
            dest=output/f"seed-{seed}-fold-{split['fold']}.joblib"
            joblib.dump(dict(vectorizer=vec,classifier=model),dest)
            run['folds'].append(dict(fold=split['fold'],train_ids=train,held_ids=held,
                permutation=permutation.tolist(),shuffled_training_labels=shuffled,
                model_sha256=digest(dest),baseline_sha256=digest(path),iterations=model.n_iter_.tolist()))
            run['predictions'].extend(dict(id=id,fold=split['fold'],prediction=str(model.classes_[p.argmax()]),
                probabilities=dict(zip(model.classes_.tolist(),p.tolist()))) for id,p in zip(held,probabilities))
        aligned={p['id']:p['prediction'] for p in run['predictions']}
        if len(run['predictions'])!=len(rows) or set(aligned)!=set(lookup):raise ValueError('Invalid OOF coverage')
        run['metrics']=metrics(rows,[aligned[r['id']] for r in rows])
        record['runs'].append(run)
        (output/'results.json').write_text(json.dumps(record,indent=2))
        print(seed,run['metrics']['accuracy'],run['metrics']['macro_f1'],flush=True)
    record['baseline_metrics']=prior['summary']['baseline']['original_metrics']
    record['limitations']=['Five corrupted-label runs are not a permutation null or significance test',
        'No global exchangeability assumption or p-value',
        'Class weighting and fold composition affect corrupted-label performance',
        'Disputed noncommercial development labels; no deployment or independent accuracy claim']
    (output/'results.json').write_text(json.dumps(record,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('data','folds','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.data,a.folds,a.output)
