"""Audit fixed development predictions; never manufacture replacement labels."""
import argparse
import json
from pathlib import Path

from hybrid_cv import digest, validate_split


def align(values, ids, assignment):
    indexed = {r['id']: r for r in values}
    if len(indexed) != len(values) or set(indexed) != set(ids):
        raise ValueError('Incomplete or duplicate prediction IDs')
    for id, row in indexed.items():
        if row['fold'] != assignment[id] or row['prediction'] not in ('LEFT','CENTER','RIGHT'):
            raise ValueError('Invalid fold or class')
    return indexed


def counts(rows):
    return dict(n=len(rows), all_wrong=sum(r['correct_n']==0 for r in rows),
                all_correct=sum(r['correct_n']==len(r['predictions']) for r in rows),
                any_correct=sum(r['correct_n']>0 for r in rows),
                disagreement=sum(len(set(r['predictions'].values()))>1 for r in rows))


def run(data, results, output):
    if output.exists():
        raise ValueError('Use a new output path')
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    paths={name:results/file for name,file in dict(hybrid='hybrid_cv_20261002.json',
        character='character_cv_20261003.json',hierarchy='hierarchy_cv_20261004.json',
        ensemble='ensemble_oof_20261002.json').items()}
    reports={name:json.loads(path.read_text()) for name,path in paths.items()}
    for name in ('hybrid','character','hierarchy'):
        if reports[name]['data_sha256']!=digest(data):
            raise ValueError('Training data fingerprint mismatch')
    if reports['ensemble']['inputs'].get(str(data))!=digest(data):
        raise ValueError('Ensemble input fingerprint mismatch')
    if digest(paths['hybrid']) not in reports['ensemble']['inputs'].values():
        raise ValueError('Ensemble component source mismatch')
    assignment={}
    reference=reports['hybrid']['folds']
    for split in reference:
        validate_split(rows,split['train_ids'],split['held_ids'])
        for id in split['held_ids']:
            if id in assignment:raise ValueError('Duplicate held ID')
            assignment[id]=split['fold']
    expected={s['fold']:(set(s['train_ids']),set(s['held_ids'])) for s in reference}
    for name in ('character','hierarchy','ensemble'):
        splits=reports[name]['component_folds_and_hashes'] if name=='ensemble' else reports[name]['folds']
        actual={s['fold']:(set(s['train_ids']),set(s['held_ids'])) for s in splits}
        if len(actual)!=len(splits) or actual!=expected:raise ValueError('Different fold membership')
    ids=[r['id'] for r in rows]
    models={name:align(reports['hybrid']['oof'][name],ids,assignment) for name in ('word','semantic','hybrid')}
    for name in ('character','hierarchy'):
        models[name]=align(reports[name]['oof'][name],ids,assignment)
    models['ensemble']=align(reports['ensemble']['predictions'],ids,assignment)
    records=[]
    for row in rows:
        predictions={name:values[row['id']]['prediction'] for name,values in models.items()}
        records.append(dict(id=row['id'],fold=assignment[row['id']],reference_label=row['label'],
            strict_agreement=row['strict_agreement'],text_sha256=row['text_sha256'],
            predictions=predictions,correct_n=sum(p==row['label'] for p in predictions.values())))
    report=dict(purpose='Fixed training-only shared-error audit, not independent accuracy',
        validation_read=False,reserved_test_read=False,labels_changed=False,release_approved=False,
        inputs={str(p):digest(p) for p in [data,*paths.values()]},models=list(models),summary=counts(records),
        by_reference={label:counts([r for r in records if r['reference_label']==label]) for label in ('LEFT','CENTER','RIGHT')},
        by_annotation={str(strict):counts([r for r in records if r['strict_agreement']==strict]) for strict in (True,False)},
        records=records,limitations=['Models share data and are not independent annotators',
        'All-wrong does not establish incorrect reference annotation',
        'Any-correct assumes perfect per-example selection, not achievable performance',
        'Repeatedly explored development data, disputed labels, noncommercial research only'])
    output.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ('summary','by_reference','by_annotation')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('data','results','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.data,a.results,a.output)
