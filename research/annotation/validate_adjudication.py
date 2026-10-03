"""Verify a third human's adjudication of two v2 reviews, for development only.

This validates self-attested provenance and exact source integrity, not human
identity or political truth. No agreement, CLI option, or input flag makes pilot
records gold, a final test, or a production approval. Uses only the stdlib.
"""
import argparse
import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

try:
    from .compare_reviews import (AXES, ATTRIBUTION, EXPOSURE, FRAMING, LABELS,
                                 POLICY, UNCERTAINTY, nonempty, timestamp, validate)
    from .spans import resolve_text, validate_spans
except ImportError:  # direct CLI invocation
    from compare_reviews import (AXES, ATTRIBUTION, EXPOSURE, FRAMING, LABELS,
                                 POLICY, UNCERTAINTY, nonempty, timestamp, validate)
    from spans import resolve_text, validate_spans

INPUT_SCHEMA = 'biascheck-human-adjudication-v1'
OUTPUT_SCHEMA = 'biascheck-adjudicated-pilot-v1'
RESOLUTION_FIELDS = set(AXES) | {'confidence', 'rationale', 'span_status',
                               'span_protocol_version', 'evidence_spans'}
SCOPE = {'development_only': True, 'final_test_eligible': False,
         'gold_labels_approved': False, 'release_approved': False}


def digest(value):
    """Canonical object digest, not a file-byte hash or identity signature."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def _inputs(first, second, manifest, snapshots):
    if not isinstance(manifest, dict) or not isinstance(manifest.get('items'), list):
        raise ValueError('Manifest must contain an items array')
    items = {}
    for item in manifest['items']:
        if (not isinstance(item, dict) or not nonempty(item.get('id'))
                or item['id'] in items
                or item.get('kind') not in {'historical_article', 'controlled_example'}
                or not isinstance(item.get('text_sha256'), str)
                or not re.fullmatch('[0-9a-f]{64}', item['text_sha256'])):
            raise ValueError('Manifest requires unique IDs, recognized kinds and exact SHA-256 hashes')
        resolve_text(item, snapshots)  # reject changed supplied text even before adjudication
        items[item['id']] = item
    a, b = validate(first, manifest, snapshots), validate(second, manifest, snapshots)
    if first['reviewer_id'].casefold() == second['reviewer_id'].casefold():
        raise ValueError('Two distinct human reviewers required; aliases are not identity authentication')
    for export in (first, second):
        exported_at = datetime.fromisoformat(export['exported_at'].replace('Z', '+00:00'))
        if any(datetime.fromisoformat(r['completed_at'].replace('Z', '+00:00')) > exported_at for r in export['annotations']):
            raise ValueError('Review completion cannot occur after its export')
    return items, a, b


def make_template(first, second, manifest, snapshots=None):
    """Make an entirely unresolved template. Does not prefill any decision."""
    items, _, _ = _inputs(first, second, manifest, snapshots)
    return {
        'schema': INPUT_SCHEMA, 'schema_version': 1,
        'pilot_id': manifest['pilot_id'], 'rubric_version': 'v2',
        'manifest_sha256': digest(manifest),
        'review_sha256': {r['reviewer_id']: digest(r) for r in (first, second)},
        **SCOPE,
        'items': [{'id': key, 'text_sha256': item['text_sha256'],
                   'status': 'unresolved', 'adjudication': None}
                  for key, item in items.items()],
    }


def _resolution(value, item, snapshots):
    if not isinstance(value, dict) or set(value) != RESOLUTION_FIELDS:
        raise ValueError('Resolution must contain exactly the documented judgment and span fields')
    relevance, framing, label = value['relevance'], value['author_framing'], value['label']
    if relevance not in {'POLITICAL', 'NONPOLITICAL', 'UNCERTAIN'} or framing not in FRAMING or label not in LABELS:
        raise ValueError('Invalid resolution relevance, framing or label')
    if ((relevance == 'POLITICAL' and (framing == 'NOT_APPLICABLE' or label != framing))
            or (relevance == 'NONPOLITICAL' and (framing != 'NOT_APPLICABLE' or label != 'NONPOLITICAL'))
            or (relevance == 'UNCERTAIN' and (framing != 'UNCERTAIN' or label != 'UNCERTAIN'))):
        raise ValueError('Resolution label must derive from relevance and author framing')
    if value['issue_policy_stance'] not in POLICY or value['attribution'] not in ATTRIBUTION:
        raise ValueError('Invalid resolution policy or attribution')
    if relevance == 'NONPOLITICAL' and value['issue_policy_stance'] not in {'NOT_ASSESSED', 'NOT_APPLICABLE', 'NO_EXPLICIT_STANCE'}:
        raise ValueError('Nonpolitical resolutions cannot carry a directional policy stance')
    if value['context_sufficiency'] not in {'SUFFICIENT', 'INSUFFICIENT', 'UNCERTAIN'} or value['uncertainty_reason'] not in UNCERTAINTY:
        raise ValueError('Invalid resolution context or uncertainty reason')
    if (label == 'UNCERTAIN') != (value['uncertainty_reason'] != 'NONE'):
        raise ValueError('Uncertain resolutions require a reason; resolved labels use NONE')
    if label in {'LEFT', 'CENTER', 'RIGHT'} and value['context_sufficiency'] != 'SUFFICIENT':
        raise ValueError('Resolved political framing requires sufficient context')
    if value['confidence'] not in {'low', 'medium', 'high'} or not nonempty(value['rationale'], 15):
        raise ValueError('Resolution requires confidence and a human rationale')
    if resolve_text(item, snapshots) is None:
        raise ValueError('Adjudication requires the exact frozen source snapshot, even without spans')
    if type(value['span_protocol_version']) is not int or value['span_protocol_version'] != 1:
        raise ValueError('Explicit span protocol version 1 required')
    return validate_spans(value, item, snapshots)


def _decision(value, item, first, second, snapshots):
    fields = {'adjudicator_id', 'adjudicator_kind', 'annotation_method', 'completed_at',
              'full_text_read', 'both_reviews_considered', 'text_context', 'prior_exposure', 'resolution'}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('Adjudication must contain exactly the documented provenance and resolution fields')
    who = value['adjudicator_id']
    if not isinstance(who, str) or not re.fullmatch(r'[A-Za-z0-9_-]{2,40}', who):
        raise ValueError('Adjudicator ID must be 2-40 letters, numbers, underscores or hyphens')
    if who.casefold() in {first['reviewer_id'].casefold(), second['reviewer_id'].casefold()}:
        raise ValueError('This protocol requires a third distinct human adjudicator')
    if value['adjudicator_kind'] != 'human' or value['annotation_method'] != 'manual':
        raise ValueError('Adjudication must be explicitly human and manual')
    if value['full_text_read'] is not True or value['both_reviews_considered'] is not True:
        raise ValueError('Adjudicator must read the complete frozen text and both reviews')
    if not timestamp(value['completed_at']):
        raise ValueError('Adjudication requires a timezone-aware completion timestamp')
    completed_at = datetime.fromisoformat(value['completed_at'].replace('Z', '+00:00'))
    if any(completed_at < datetime.fromisoformat(r['exported_at'].replace('Z', '+00:00')) for r in (first, second)):
        raise ValueError('Adjudication cannot precede the review exports it considered')
    context = value['text_context']
    if (not isinstance(context, dict) or context.get('scope') != 'complete_frozen_text'
            or context.get('text_sha256') != item['text_sha256']
            or type(context.get('external_context_used')) is not bool):
        raise ValueError('Adjudicator must disclose exact frozen context and external use')
    if context['external_context_used'] and not nonempty(context.get('external_context_notes'), 10):
        raise ValueError('Adjudicator external context requires notes')
    exposure = value['prior_exposure']
    if (not isinstance(exposure, dict) or any(type(exposure.get(k)) is not bool for k in EXPOSURE)
            or exposure['other_reviewer_answers'] is not True
            or not nonempty(exposure.get('notes'), 10)):
        raise ValueError('Adjudicator must disclose model/legacy exposure and seeing both human reviews, with notes')
    return _resolution(value['resolution'], item, snapshots)


def validate_adjudication(first, second, manifest, document, snapshots=None):
    """Return provenance-bearing development records; never auto-resolve agreement."""
    items, a, b = _inputs(first, second, manifest, snapshots)
    template = make_template(first, second, manifest, snapshots)
    if not isinstance(document, dict) or set(document) != set(template):
        raise ValueError('Unexpected or missing adjudication document fields')
    if type(document['schema_version']) is not int:
        raise ValueError('Adjudication schema_version must be an integer')
    for field in set(template) - {'items'}:
        if type(document[field]) is not type(template[field]) or document[field] != template[field]:
            raise ValueError('Adjudication provenance or development-only scope mismatch: ' + field)
    if not isinstance(document['items'], list):
        raise ValueError('Adjudication items must be an array')
    supplied = {}
    for row in document['items']:
        if (not isinstance(row, dict) or set(row) != {'id', 'text_sha256', 'status', 'adjudication'}
                or not isinstance(row.get('id'), str) or row['id'] not in items or row['id'] in supplied):
            raise ValueError('Adjudication requires unique known IDs and documented fields')
        if row['text_sha256'] != items[row['id']]['text_sha256']:
            raise ValueError('Adjudication source hash mismatch')
        if row['status'] not in {'unresolved', 'adjudicated'}:
            raise ValueError('Status must be unresolved or adjudicated')
        if row['status'] == 'unresolved' and row['adjudication'] is not None:
            raise ValueError('Unresolved items cannot carry a resolution')
        supplied[row['id']] = row
    if set(supplied) != set(items):
        raise ValueError('Every manifest item must remain explicit, including unresolved or missing reviews')

    raw_a = {r['id']: r for r in first['annotations']}
    raw_b = {r['id']: r for r in second['annotations']}
    records = []
    for key, item in items.items():
        row, pair = supplied[key], [a.get(key), b.get(key)]
        flags, disagreement_axes = [], []
        if any(r is None for r in pair):
            flags.append('missing_or_skipped_review')
        else:
            disagreement_axes = [f for f in AXES if pair[0][f] != pair[1][f]]
            if any(pair[0].get(f) != pair[1].get(f) for f in ('span_status', 'evidence_spans')):
                disagreement_axes.append('evidence_spans')
            if pair[0]['review_phase'] != pair[1]['review_phase'] or pair[0].get('rubric_freeze_id') != pair[1].get('rubric_freeze_id'):
                flags.append('different_review_round_or_freeze')
        for review in [r for r in pair if r is not None]:
            if any(review['prior_exposure'][f] for f in EXPOSURE):
                flags.append('prior_reviewer_exposure')
            if review['text_context']['external_context_used']:
                flags.append('reviewer_external_context')
            if review['review_phase'] == 'post_discussion_rereview':
                flags.append('post_discussion_rereview')
        source_text = resolve_text(item, snapshots)
        if source_text is None:
            flags.append('missing_source_snapshot')
        decision, verification = None, None
        if row['status'] == 'adjudicated':
            if any(r is None for r in pair):
                raise ValueError('Adjudication requires two completed reviews for ' + key)
            decision = row['adjudication']
            verification = _decision(decision, item, first, second, snapshots)
            if decision['text_context']['external_context_used']:
                flags.append('adjudicator_external_context')
            if decision['prior_exposure']['model_predictions'] or decision['prior_exposure']['legacy_labels']:
                flags.append('adjudicator_model_or_legacy_exposure')
            if decision['resolution']['label'] == 'UNCERTAIN':
                flags.append('adjudicated_primary_uncertainty')
            if decision['resolution']['span_status'] == 'NOT_ASSESSED':
                flags.append('adjudicated_spans_unassessed')
        records.append({
            'id': key, 'text_sha256': item['text_sha256'],
            'source': {k: copy.deepcopy(v) for k, v in item.items() if k != 'text'},
            **SCOPE,
            'status': 'human_adjudicated_development' if decision else 'unresolved',
            'source_verified': source_text is not None,
            'reviewers': [first['reviewer_id'], second['reviewer_id']],
            'original_reviews': [copy.deepcopy(raw_a.get(key)), copy.deepcopy(raw_b.get(key))],
            'disagreement_axes': disagreement_axes, 'limitations': sorted(set(flags)),
            'adjudication': copy.deepcopy(decision), 'span_verification': verification,
        })
    return {
        'schema': OUTPUT_SCHEMA, 'schema_version': 1, 'pilot_id': manifest['pilot_id'],
        'rubric_version': 'v2', **SCOPE,
        'provenance_basis': 'self-attested human manual work; identities and political correctness are not authenticated',
        'hash_algorithm': 'sha256_canonical_utf8_json_sorted_keys_v1',
        'manifest_sha256': digest(manifest), 'review_sha256': template['review_sha256'],
        'adjudication_sha256': digest(document),
        'review_export_metadata': [{k: copy.deepcopy(v) for k, v in r.items() if k != 'annotations'} for r in (first, second)],
        'summary': {'items_n': len(records),
                    'human_adjudicated_development_n': sum(r['status'] == 'human_adjudicated_development' for r in records),
                    'unresolved_n': sum(r['status'] == 'unresolved' for r in records)},
        'limitations': [
            'Every pilot item remains development material, including blinded agreements and adjudications.',
            'Original human and adjudicator exposure/context disclosures are retained, not erased by adjudication.',
            'Exact source and span verification establish textual integrity, not correct political judgments.',
            'Reviewer aliases, timestamps and manual attestations cannot authenticate distinct real humans.',
            'Historical training overlap and redistribution/training rights are not established by this converter.',
            'Natural articles and AI-authored controls must be reported separately; no population accuracy claim.',
        ],
        'records': records,
    }


def _read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON value: ' + value)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--second', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('pilot_manifest_v2.json'))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--template', action='store_true', help='Write only unresolved placeholders, no labels')
    mode.add_argument('--adjudication', type=Path, help='Explicit third-human adjudication document')
    parser.add_argument('--snapshots', type=Path, help='Pinned source dataset data/jsons folder')
    parser.add_argument('--output', type=Path, required=True, help='New file; existing output is never overwritten')
    args = parser.parse_args()
    manifest, first, second = _read(args.manifest), _read(args.first), _read(args.second)
    snapshots = {}
    if args.snapshots:
        for item in manifest['items']:
            if item.get('dataset_id'):
                dataset_id = str(item['dataset_id'])
                if not re.fullmatch(r'[A-Za-z0-9_-]+', dataset_id):
                    raise ValueError('Unsafe dataset snapshot ID')
                path = args.snapshots / (dataset_id + '.json')
                if path.exists():
                    data = _read(path)
                    if str(data.get('ID')) != dataset_id or not isinstance(data.get('content_original'), str):
                        raise ValueError('Snapshot ID/content mismatch')
                    snapshots[item['id']] = data['content_original'].strip()
    output = (make_template(first, second, manifest, snapshots) if args.template else
              validate_adjudication(first, second, manifest, _read(args.adjudication), snapshots))
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


if __name__ == '__main__':
    main()
