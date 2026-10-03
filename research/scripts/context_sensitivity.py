"""Frozen training-OOF title/body sensitivity, without inherited view labels."""
import argparse
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
from hybrid_cv import validate_split
from corpus_experiment import metrics


def views(text):
    parts=text.split('\n\n')
    if len(parts)!=4 or not all(p.strip() for p in parts):
        raise ValueError('Expected title plus three nonempty snippets')
    return {'full':text,'title':parts[0],'body':'\n\n'.join(parts[1:])}


def total_variation(first,second):
    if set(first)!=set(second):raise ValueError('Class labels differ')
    return sum(abs(first[k]-second[k]) for k in first)/2


def run(data,folds,output):
    if output.exists():raise ValueError('Use a new output directory')
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    prior=json.loads((folds/'training_results.json').read_text())
    data_hash=hashlib.sha256(data.read_bytes()).hexdigest()
    if data_hash!=prior['input_sha256']:raise ValueError('Input hash mismatch')
    by_id={r['id']:r for r in rows}
    baseline={r['id']:r['prediction'] for r in prior['oof']['baseline']}
    record={'purpose':'Frozen training-OOF context sensitivity, not altered-view accuracy',
        'release_approved':False,'validation_read':False,'reserved_test_read':False,
        'data_sha256':data_hash,'fold_manifest_sha256':hashlib.sha256((folds/'training_results.json').read_bytes()).hexdigest(),
        'definitions':{'title':'First paragraph','body':'Remaining three snippets','total_variation':'Half L1 distance between probability vectors'},
        'folds':[],'predictions':[]}
    for split in prior['folds']:
        validate_split(rows,split['train_ids'],split['held_ids'])
        path=folds/('fold-'+str(split['fold'])+'-baseline.joblib')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=split['models']['baseline']['model_sha256']:raise ValueError('Model hash mismatch')
        saved=joblib.load(path);model=saved['classifier'];vectorizer=saved['vectorizer']
        record['folds'].append({'fold':split['fold'],'train_ids':split['train_ids'],'held_ids':split['held_ids'],'model_sha256':digest})
        for id in split['held_ids']:
            item={'id':id,'fold':split['fold'],'views':{}}
            for name,text in views(by_id[id]['text']).items():
                features=vectorizer.transform([text]);scores=model.predict_proba(features)[0]
                item['views'][name]={'prediction':str(model.classes_[np.argmax(scores)]),
                    'probabilities':dict(zip(model.classes_.tolist(),scores.tolist())),
                    'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'word_count':len(text.split()),'nonzero_features':features.nnz}
            if item['views']['full']['prediction']!=baseline[id]:raise ValueError('Full prediction failed to reproduce baseline')
            record['predictions'].append(item)
    aligned={r['id']:r for r in record['predictions']}
    if len(aligned)!=len(rows) or len(record['predictions'])!=len(rows) or set(aligned)!=set(by_id):raise ValueError('Invalid OOF coverage')
    record['full_metrics']=metrics(rows,[aligned[r['id']]['views']['full']['prediction'] for r in rows])
    record['sensitivity']={}
    for name in ('title','body'):
        changed=[r for r in record['predictions'] if r['views'][name]['prediction']!=r['views']['full']['prediction']]
        record['sensitivity'][name]={'n':len(rows),'changed_n':len(changed),'changed_fraction':len(changed)/len(rows),
            'mean_probability_total_variation':float(np.mean([total_variation(r['views'][name]['probabilities'],r['views']['full']['probabilities']) for r in record['predictions']])),
            'zero_feature_n':sum(r['views'][name]['nonzero_features']==0 for r in record['predictions'])}
    record['cautions']=['Removing content changes evidence; flips are not inherently errors',
        'Article reference labels are not assigned to title/body views; no view accuracy computed',
        'Training OOF development reused; event strings do not prove independent event families',
        'Noncommercial disputed corpus remains research-only; no model or policy changes']
    output.mkdir(parents=True)
    (output/'results.json').write_text(json.dumps(record,indent=2))
    (output/'browser_views.json').write_text(json.dumps([{'id':rows[0]['id']+'-'+name,'text':text} for name,text in views(rows[0]['text']).items()],indent=2))
    print(json.dumps(record['sensitivity'],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('data','folds','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();run(args.data,args.folds,args.output)
