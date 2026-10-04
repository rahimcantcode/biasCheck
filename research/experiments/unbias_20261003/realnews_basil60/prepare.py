"""Freeze existing human labels, source identities, and an overlap-audited sample."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
BASIL_REV = '4fdbc4f68d5ddae648990063cb6dd11424d96222'
TRAIN_REV = '2e0a842ca594549a510ac527e2222b82d04b9784'
TRAIN_SHA = 'ca1bf39446b8031d57c5c487790a8a69eff62078aad0ccb565cd7f9a8a861d6d'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def words(text):
    return re.findall(r'[^\W_]+', text.casefold(), flags=re.UNICODE)


def ngrams(tokens, n=13):
    return {' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)}


def prepare(data):
    root = data / 'basil'
    provenance = json.loads((data / 'basil_provenance.json').read_text())
    assert provenance['revision'] == BASIL_REV
    train_bytes = (data / 'train_4.json').read_bytes()
    assert sha(train_bytes) == TRAIN_SHA
    train = json.loads(train_bytes)
    assert len(train) == 5000
    stats = Counter()
    candidates = []
    for af in sorted(root.glob('annotations/**/*.json')):
        a = json.loads(af.read_text())
        tf = root / 'articles' / af.parent.name / af.name.replace('_ann', '')
        article = json.loads(tf.read_text())
        assert a['uuid'] == article['uuid']
        sentences = sum(article['body-paragraphs'], [])
        annotations = a['phrase-level-annotations']
        stats['articles'] += 1
        stats['body_sentences'] += len(sentences)
        stats['title_spans_excluded'] += sum(x['id'] == 'title' for x in annotations)
        # Audit every body annotation, not just those ultimately selected.
        valid_by_sentence = defaultdict(lambda: True)
        for x in annotations:
            if x['id'] == 'title':
                continue
            assert re.fullmatch(r'p\d+', x['id'])
            index = int(x['id'][1:])
            assert 0 <= index < len(sentences)
            good = (0 <= x['start'] < x['end'] <= len(sentences[index])
                    and sentences[index][x['start']:x['end']] == x['txt'])
            valid_by_sentence[index] &= good
            stats['valid_body_spans' if good else 'invalid_body_spans'] += 1
        for index, text in enumerate(sentences):
            if not valid_by_sentence[index]:
                stats['excluded_invalid_sentence'] += 1
                continue
            if not 15 <= len(text.split()) <= 80:
                stats['excluded_length_sentence'] += 1
                continue
            gold = [x for x in annotations if x['id'] == f'p{index}']
            assert all(x['bias'] in {'lex', 'inf'} and x['quote'] in {'yes', 'no'} for x in gold)
            stratum = ('lexical' if any(x['bias'] == 'lex' for x in gold)
                       else 'informational' if gold else 'unannotated')
            uid = f'{article["uuid"]}:p{index}'
            candidates.append({
                'id': uid, 'text': text, 'source_sha256': sha(text.encode()),
                'stratum': stratum, 'event_id': article['triplet-uuid'],
                'article_id': article['uuid'], 'article_file': str(tf.relative_to(root)),
                'annotation_file': str(af.relative_to(root)), 'sentence_index': index,
                'article_sha256': sha(tf.read_bytes()), 'annotation_sha256': sha(af.read_bytes()),
                'publisher': article['source'], 'date': article['date'],
                'word_count': len(text.split()),
                'gold': [{'start': x['start'], 'end': x['end'], 'bias': x['bias'],
                          'quoted': x['quote'] == 'yes', 'speaker': x['speaker'],
                          'target': x['target'], 'polarity': x['polarity']} for x in gold],
            })
    # Index candidate shingles; never retain all training shingles in memory.
    index = defaultdict(set)
    for c in candidates:
        for gram in ngrams(words(c['text'])):
            index[gram].add(c['id'])
    overlap = defaultdict(set)
    normalized_training = []
    for row in train:
        tokens = words(row['article_text'])
        normalized_training.append(' '.join(tokens))
        for gram in ngrams(tokens):
            for uid in index.get(gram, ()):
                overlap[uid].add(row['unique_id'])
    eligible = [c for c in candidates if c['id'] not in overlap]
    selected = []
    used_events = set()
    for stratum in ['lexical', 'informational', 'unannotated']:
        group = sorted((c for c in eligible if c['stratum'] == stratum),
                       key=lambda c: sha(('basil60-v1|' + c['id']).encode()))
        count = 0
        for c in group:
            if c['event_id'] in used_events:
                continue
            selected.append(c)
            used_events.add(c['event_id'])
            count += 1
            if count == 20:
                break
        assert count == 20, f'Insufficient event-distinct cases for {stratum}'
    selected.sort(key=lambda c: sha(('basil60-order-v1|' + c['id']).encode()))
    exact = []
    for c in selected:
        normalized = ' '.join(words(c['text']))
        if any(normalized in row for row in normalized_training):
            exact.append(c['id'])
    assert not exact, 'Selected sentence exactly overlaps training data'
    assert len({c['source_sha256'] for c in selected}) == 60
    stats['eligible_before_overlap'] = len(candidates)
    stats['excluded_13gram_overlap'] = len(overlap)
    stats['eligible_after_overlap'] = len(eligible)
    stats['selected_exact_normalized_training_containment'] = len(exact)
    fixture = {'schema': 'basil60-realnews-v1', 'cases': selected}
    raw = json.dumps(fixture, ensure_ascii=False, indent=2).encode() + b'\n'
    case_path = data / 'cases.json'
    if case_path.exists():
        assert case_path.read_bytes() == raw, 'Refusing to overwrite different sample'
    else:
        case_path.write_bytes(raw)
    manifest = {
        'schema': fixture['schema'], 'basil_revision': BASIL_REV,
        'basil_archive_sha256': provenance['archive_sha256'],
        'training_dataset_revision': TRAIN_REV, 'training_file_sha256': TRAIN_SHA,
        'training_rows_checked': len(train), 'fixture_sha256': sha(raw),
        'protocol_sha256': sha((HERE / 'PROTOCOL.md').read_bytes()),
        'annotation_source': 'Published BASIL release-2 human reference annotations, unchanged',
        'new_human_reviews': 0, 'training_independence_proven': False,
        'audit_counts': dict(stats),
        'overlap_exclusions': [{'id': k, 'training_ids': sorted(v)} for k, v in sorted(overlap.items())],
        'sample_counts': dict(Counter(c['stratum'] for c in selected)),
        'publishers': dict(Counter(c['publisher'] for c in selected)),
        'event_count': len(used_events),
        'human_span_count': sum(len(c['gold']) for c in selected),
        'quoted_human_span_count': sum(g['quoted'] for c in selected for g in c['gold']),
        'cases': [{k: v for k, v in c.items() if k != 'text'} for c in selected],
    }
    output = HERE / 'sample_manifest.json'
    serialized = json.dumps(manifest, indent=2) + '\n'
    if output.exists():
        assert output.read_text() == serialized, 'Refusing to overwrite different manifest'
    else:
        output.write_text(serialized)
    print(json.dumps({k: v for k, v in manifest.items() if k not in {'cases', 'overlap_exclusions'}}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    prepare(parser.parse_args().data)
