import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('pilot_passages', Path(__file__).parents[1] / 'research/scripts/pilot_passages.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    text = '  ' + 'word ' * 80 + '\n\n' + 'other ' * 200 + '\n\nshort'
    manifest = {'pilot_id': 'fixture', 'dataset_revision': 'fixture', 'items': [
        {'id': 'P1', 'kind': 'historical_article', 'text_sha256': module.digest(text)}]}
    return manifest, [{'id': 'P1', 'text': text}]


def test_exact_reproducible_span_and_no_label():
    manifest, snapshots = fixture()
    report, passages = module.build(manifest, snapshots)
    row = report['records'][0]
    assert row['eligible_paragraphs'] == 2
    assert row['word_count'] in (80, 200)
    assert passages[0]['text'] == snapshots[0]['text'][row['start']:row['end']]
    assert row['text_sha256'] == module.digest(passages[0]['text'])
    assert row['label'] is None and not row['human_reviewed']
    assert module.build(manifest, snapshots) == (report, passages)


def test_excluded_short_parent():
    manifest, snapshots = fixture()
    snapshots[0]['text'] = 'short'
    manifest['items'][0]['text_sha256'] = module.digest('short')
    report, passages = module.build(manifest, snapshots)
    assert not passages and len(report['exclusions']) == 1


@pytest.mark.parametrize('mutation', ['duplicate', 'missing', 'hash'])
def test_invalid_snapshots(mutation):
    manifest, snapshots = fixture()
    if mutation == 'duplicate':
        snapshots.append(snapshots[0])
    elif mutation == 'missing':
        snapshots.clear()
    else:
        snapshots[0]['text'] += 'changed'
    with pytest.raises(ValueError):
        module.build(manifest, snapshots)
