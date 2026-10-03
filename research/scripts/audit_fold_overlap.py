"""Training-only cross-fold overlap candidates, not proof of leakage."""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_development_overlap import overlap, shingles
from boilerplate_ablation import strip_footers
from hybrid_cv import digest, validate_split


def run(data, features, folds, output):
    if output.exists():
        raise ValueError('Use a new output path')
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    metadata = json.loads(features.with_suffix('.json').read_text())
    prior = json.loads(folds.read_text())
    ids = [r['id'] for r in rows]
    if metadata['records']['train']['ids'] != ids or metadata['records']['train']['data_sha256'] != digest(data) or prior['input_sha256'] != digest(data):
        raise ValueError('Training provenance mismatch')
    with np.load(features, allow_pickle=False) as archive:
        vectors = archive['train']
    if vectors.shape != (len(rows), 384) or not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5):
        raise ValueError('Invalid normalized training embeddings')
    assignment = {}
    for split in prior['folds']:
        validate_split(rows, split['train_ids'], split['held_ids'])
        for id in split['held_ids']:
            if id in assignment:
                raise ValueError('Repeated held ID')
            assignment[id] = split['fold']
    if set(assignment) != set(ids):
        raise ValueError('Missing held IDs')
    raw = [shingles(r['text']) for r in rows]
    clean = [shingles(strip_footers(r['text'])[0]) for r in rows]
    if any(not grams for grams in raw + clean):
        raise ValueError('Cannot assess lexical overlap for fewer than five tokens')
    cosine = vectors @ vectors.T
    pairs = []
    for i, a in enumerate(rows):
        for j in range(i + 1, len(rows)):
            b = rows[j]
            if assignment[a['id']] == assignment[b['id']]:
                continue
            score = overlap(clean[i], clean[j])
            reasons = []
            if cosine[i, j] >= .85:
                reasons.append('semantic_similarity')
            if score['jaccard'] >= .3:
                reasons.append('clean_lexical_similarity')
            if score['shorter_containment'] >= .5 and score['shared_5grams'] >= 20:
                reasons.append('clean_containment')
            pairs.append(dict(first=a['id'], second=b['id'], first_fold=assignment[a['id']],
                              second_fold=assignment[b['id']], cosine=float(cosine[i,j]),
                              raw=overlap(raw[i],raw[j]), clean=score, flag_reasons=reasons))
    flagged = [p for p in pairs if p['flag_reasons']]
    exposed = sorted({p[k] for p in flagged for k in ('first','second')})
    result = dict(purpose='Training-only heuristic cross-fold overlap audit; not proof of leakage',
                  validation_read=False, reserved_test_read=False, split_changes=False,
                  data_sha256=digest(data), feature_container_sha256=digest(features),
                  feature_metadata_sha256=digest(features.with_suffix('.json')),
                  folds_sha256=digest(folds), selection_uses_labels=False,
                  shingling='Unique contiguous five-word tuples from lowercase regex word tokens',
                  containment='Shared shingle count divided by smaller set size; symmetric',
                  empty_shingle_sets='Rejected before analysis',
                  thresholds=dict(cosine=.85, clean_jaccard=.3, clean_containment=.5, minimum_shared_5grams=20),
                  row_count=len(rows), cross_fold_pair_count=len(pairs),
                  flagged_pair_count=len(flagged), exposed_ids=exposed,
                  exposed_by_fold={str(f):sum(assignment[id]==f for id in exposed) for f in sorted(set(assignment.values()))},
                  flagged_pairs=sorted(flagged,key=lambda p:p['cosine'],reverse=True), all_pairs=pairs,
                  limitations=['Similar topics, quotations and style are not duplicate proof',
                               'No flags does not prove independence',
                               'Footer stripping affects lexical overlap only; semantic embeddings remain raw',
                               'No human event-family adjudication or fold repair performed'])
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:result[k] for k in ('row_count','cross_fold_pair_count','flagged_pair_count','exposed_ids','exposed_by_fold')},indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    for name in ('data','features','folds','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    run(a.data,a.features,a.folds,a.output)
