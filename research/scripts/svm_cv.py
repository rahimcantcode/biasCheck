"""Fixed linear SVM on previously frozen training-only word features."""
import argparse
import json
from pathlib import Path

import joblib
import sklearn
from sklearn.svm import LinearSVC

from corpus_experiment import metrics
from hybrid_cv import digest, validate_split


def run(data, folds, output):
    if output.exists():
        raise ValueError('Use a new output directory')
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    prior=json.loads((folds/'training_results.json').read_text())
    if digest(data)!=prior['input_sha256']:raise ValueError('Training fingerprint mismatch')
    lookup={r['id']:r for r in rows}
    settings=dict(C=1,class_weight='balanced',loss='squared_hinge',penalty='l2',
                  dual='auto',tol=1e-4,max_iter=10000,random_state=20261001)
    report=dict(purpose='Fixed training-only exploratory SVM comparison; not independent accuracy',
        validation_read=False,reserved_test_read=False,release_approved=False,
        data_sha256=digest(data),fold_manifest_sha256=digest(folds/'training_results.json'),
        settings=settings,sklearn_version=sklearn.__version__,folds=[],oof={'word':[],'svm':[]})
    output.mkdir(parents=True)
    (output/'protocol.json').write_text(json.dumps(report,indent=2))
    for split in prior['folds']:
        train,held=split['train_ids'],split['held_ids']
        validate_split(rows,train,held)
        path=folds/f"fold-{split['fold']}-baseline.joblib"
        if digest(path)!=split['models']['baseline']['model_sha256']:raise ValueError('Baseline mismatch')
        saved=joblib.load(path);vec=saved['vectorizer']
        model=LinearSVC(**settings).fit(vec.transform([lookup[i]['text'] for i in train]),[lookup[i]['label'] for i in train])
        h=vec.transform([lookup[i]['text'] for i in held])
        scores=model.decision_function(h);predicted=model.predict(h)
        baseline=saved['classifier'].predict(h)
        dest=output/f"fold-{split['fold']}.joblib"
        joblib.dump(dict(vectorizer=vec,classifier=model),dest)
        report['folds'].append(dict(fold=split['fold'],train_ids=train,held_ids=held,
            baseline_sha256=digest(path),model_sha256=digest(dest),iterations=int(model.n_iter_)))
        for id,p,score,b in zip(held,predicted,scores,baseline):
            report['oof']['svm'].append(dict(id=id,fold=split['fold'],prediction=str(p),
                decision_scores=dict(zip(model.classes_.tolist(),score.tolist())),score_type='uncalibrated_svm_decision'))
            report['oof']['word'].append(dict(id=id,fold=split['fold'],prediction=str(b)))
        (output/'training_results.json').write_text(json.dumps(report,indent=2))
        print('completed fold',split['fold'],flush=True)
    report['metrics']={};maps={}
    for name,predictions in report['oof'].items():
        maps[name]={r['id']:r['prediction'] for r in predictions}
        if len(predictions)!=len(rows) or set(maps[name])!=set(lookup):raise ValueError('Invalid OOF coverage')
        report['metrics'][name]=metrics(rows,[maps[name][r['id']] for r in rows])
    report['corrected_ids']=[r['id'] for r in rows if maps['word'][r['id']]!=r['label'] and maps['svm'][r['id']]==r['label']]
    report['regressed_ids']=[r['id'] for r in rows if maps['word'][r['id']]==r['label'] and maps['svm'][r['id']]!=r['label']]
    (output/'training_results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report['metrics'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('data','folds','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.data,a.folds,a.output)
