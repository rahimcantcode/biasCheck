"""Fixed nested group-subsampling learning curve on training folds only."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from corpus_experiment import metrics
from hybrid_cv import validate_split


def subsets(rows, seed):
    groups=sorted({r['event'] for r in rows})
    rng=np.random.default_rng(seed)
    rng.shuffle(groups)
    return {str(fraction):[r for r in rows if r['event'] in set(groups[:math.ceil(fraction*len(groups))])]
            for fraction in (.25,.5,1.)}


def run(data, folds, output, group_seed=20261002):
    if output.exists():raise ValueError('Use a new output directory')
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    prior=json.loads(folds.read_text())
    digest=hashlib.sha256(data.read_bytes()).hexdigest()
    if digest!=prior['input_sha256']:raise ValueError('Training hash mismatch')
    lookup={r['id']:r for r in rows}
    record={'purpose':'Training-only exploratory learning curve; not independent accuracy',
        'validation_read':False,'reserved_test_read':False,'release_approved':False,
        'data_sha256':digest,'fold_manifest_sha256':hashlib.sha256(folds.read_bytes()).hexdigest(),
        'settings':{'fractions_of_event_groups':[.25,.5,1.], 'group_seed':str(group_seed)+'+fold',
                    'vectorizer':'word1,2; min_df2; max_features20000; sublinear_tf; fit subset only',
                    'classifier':'LogisticRegression C1 balanced max_iter1000 random_state20261001',
                    'orderings_per_fold':1},
        'runtime':{'numpy':np.__version__,'sklearn':sklearn.__version__,'joblib':joblib.__version__},
        'folds':[], 'oof':{str(f):[] for f in (.25,.5,1.)}}
    output.mkdir(parents=True)
    (output/'protocol.json').write_text(json.dumps(record,indent=2))
    for split in prior['folds']:
        validate_split(rows,split['train_ids'],split['held_ids'])
        train=[lookup[id] for id in split['train_ids']]
        held=[lookup[id] for id in split['held_ids']]
        fold={'fold':split['fold'],'held_ids':split['held_ids'],'subsets':{}}
        for fraction, selected in subsets(train,group_seed+split['fold']).items():
            counts=Counter(r['label'] for r in selected)
            if set(counts)!={'LEFT','CENTER','RIGHT'}:raise ValueError('Subset lacks a class; do not search another seed')
            vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=20000,sublinear_tf=True)
            features=vectorizer.fit_transform([r['text'] for r in selected])
            model=LogisticRegression(C=1,class_weight='balanced',max_iter=1000,random_state=20261001)
            model.fit(features,[r['label'] for r in selected])
            probabilities=model.predict_proba(vectorizer.transform([r['text'] for r in held]))
            predictions=model.classes_[probabilities.argmax(axis=1)].tolist()
            path=output/('fold-'+str(split['fold'])+'-fraction-'+fraction+'.joblib')
            joblib.dump({'vectorizer':vectorizer,'classifier':model},path)
            fold['subsets'][fraction]={'train_ids':[r['id'] for r in selected],'n':len(selected),
                'groups':len({r['event'] for r in selected}),'label_counts':dict(counts),
                'vocabulary_n':len(vectorizer.vocabulary_),'iterations':model.n_iter_.tolist(),
                'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'metrics':metrics(held,predictions)}
            record['oof'][fraction].extend({'id':r['id'],'fold':split['fold'],'prediction':p,
                'probabilities':dict(zip(model.classes_.tolist(),scores.tolist()))} for r,p,scores in zip(held,predictions,probabilities))
        record['folds'].append(fold)
    record['metrics']={}
    for fraction,values in record['oof'].items():
        aligned={r['id']:r['prediction'] for r in values}
        if len(values)!=len(rows) or set(aligned)!=set(lookup):raise ValueError('Invalid OOF coverage')
        record['metrics'][fraction]=metrics(rows,[aligned[r['id']] for r in rows])
    record['cautions']=['Single ordering per fold, not replicated learning-curve uncertainty',
        'Group fractions differ from article fractions; subsets vary in class/topic mix',
        'Event strings do not establish event-family independence',
        'Prior development influenced design; no extrapolation to high accuracy',
        'Disputed noncommercial corpus labels; research-only models']
    (output/'training_results.json').write_text(json.dumps(record,indent=2))
    print(json.dumps({f:{'accuracy':m['accuracy'],'macro_f1':m['macro_f1']} for f,m in record['metrics'].items()},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('data','folds','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--group-seed',type=int,default=20261002)
    a=p.parse_args();run(a.data,a.folds,a.output,a.group_seed)
