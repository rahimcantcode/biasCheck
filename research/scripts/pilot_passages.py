"""Prepare unlabeled development passages without altering the frozen pilot."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def build(manifest, snapshots):
    items = manifest['items']
    ids = [r['id'] for r in items]
    snapshot_ids = [r['id'] for r in snapshots]
    if len(set(ids)) != len(ids) or len(set(snapshot_ids)) != len(snapshot_ids):
        raise ValueError('Duplicate IDs')
    if set(ids) != set(snapshot_ids):
        raise ValueError('Snapshot IDs must match the frozen pilot')
    texts = {r['id']: r['text'] for r in snapshots}
    records, exclusions, passages = [], [], []
    for item in items:
        text = texts[item['id']]
        if digest(text) != item['text_sha256']:
            raise ValueError('Snapshot hash mismatch: ' + item['id'])
        if item['kind'] != 'historical_article':
            continue
        candidates = []
        # Same blank-line paragraph convention as the application, no normalization.
        for match in re.finditer(r'[^\n]+(?:\n(?!\s*\n)[^\n]+)*', text):
            start, end = match.span()
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            words = len(text[start:end].split())
            if 80 <= words <= 200:
                rank = digest(f"{item['id']}:{start}:{end}")
                candidates.append((rank, start, end, words))
        if not candidates:
            exclusions.append({'parent_id': item['id'], 'reason': 'no_80_200_word_paragraph'})
            continue
        rank, start, end, words = min(candidates)
        passage = text[start:end]
        row = {'id': item['id'] + '-passage-v1', 'parent_id': item['id'],
               'split_group': item['id'], 'parent_sha256': item['text_sha256'],
               'start': start, 'end': end, 'offset_unit': 'unicode_codepoint',
               'word_count': words, 'text_sha256': digest(passage),
               'eligible_paragraphs': len(candidates), 'selection_rank': rank,
               'human_reviewed': False, 'label': None}
        records.append(row)
        passages.append({'id': row['id'], 'text': passage})
    return {'purpose': 'Unlabeled rubric development; not an independent evaluation',
            'parent_pilot_id': manifest['pilot_id'],
            'dataset_revision': manifest['dataset_revision'],
            'selection': 'Lowest SHA256(parent_id:start:end), one 80-200 word paragraph per parent',
            'human_reviewed': False, 'release_approved': False, 'reserved_test_read': False,
            'records': records, 'exclusions': exclusions,
            'cautions': ['Eligibility introduces length/format selection bias',
                         'Paragraphs may lose attribution or necessary surrounding context',
                         'Parent grouping does not ensure event, publisher or training independence',
                         'Historical sources and reuse-rights limitations remain',
                         'No inherited article labels; annotate passage relevance and stance separately']}, passages


def main():
    parser = argparse.ArgumentParser()
    for name in ('manifest', 'snapshots', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    report, passages = build(json.loads(args.manifest.read_text()), json.loads(args.snapshots.read_text()))
    report['input_sha256'] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                              for name, path in [('manifest', args.manifest), ('snapshots', args.snapshots)]}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    (args.output / 'texts.json').write_text(json.dumps(passages, indent=2) + '\n')
    (args.output / 'browser.json').write_text(json.dumps(passages[:2], indent=2) + '\n')
    print(json.dumps({'selected': len(passages), 'excluded': len(report['exclusions'])}))


if __name__ == '__main__':
    main()
