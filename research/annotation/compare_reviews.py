"""Validate v2 human-review provenance and report agreement, never machine gold.

Self-attestation is auditable metadata, not authentication of a human identity.
Legacy v1 exports must be preserved and re-reviewed, never silently upgraded.
"""
import argparse
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    from .spans import validate_spans, span_agreement
except ImportError:  # direct CLI invocation
    from spans import validate_spans, span_agreement

LABELS = {'LEFT', 'CENTER', 'RIGHT', 'NONPOLITICAL', 'UNCERTAIN'}
FRAMING = {'LEFT', 'CENTER', 'RIGHT', 'UNCERTAIN', 'NOT_APPLICABLE'}
POLICY = {'NOT_ASSESSED', 'NO_EXPLICIT_STANCE', 'LEFT', 'CENTER', 'RIGHT', 'MIXED', 'UNCERTAIN', 'NOT_APPLICABLE'}
ATTRIBUTION = {'AUTHOR_NARRATION', 'QUOTED_SPEAKERS_ONLY', 'MIXED_AUTHOR_AND_QUOTES', 'NO_STANCE_EXPRESSED', 'UNCLEAR'}
UNCERTAINTY = {'NONE', 'INSUFFICIENT_CONTEXT', 'MIXED_AUTHOR_POSITIONS', 'ATTRIBUTION_UNCLEAR', 'SARCASM_OR_AMBIGUITY', 'OUTSIDE_US_SCHEME', 'OTHER'}
EXPOSURE = ('model_predictions', 'legacy_labels', 'other_reviewer_answers')
AXES = ('relevance', 'author_framing', 'issue_policy_stance', 'attribution', 'context_sufficiency', 'uncertainty_reason', 'label')
PHASES = {'initial_independent_10', 'post_discussion_rereview', 'frozen_main'}


def nonempty(value, minimum=1):
    return isinstance(value, str) and len(value.strip()) >= minimum


def timestamp(value):
    if not nonempty(value):
        return False
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is not None
    except ValueError:
        return False


def validate(review, manifest, snapshots=None):
    if not isinstance(review, dict) or not isinstance(manifest, dict):
        raise ValueError('Review and manifest must be JSON objects')
    if (manifest.get('schema_version') != 2 or manifest.get('rubric_version') != 'v2'
            or review.get('schema_version') != 2 or review.get('rubric_version') != 'v2'
            or review.get('pilot_id') != manifest.get('pilot_id')):
        raise ValueError('Pilot or rubric mismatch: legacy v1 requires a new v2 human review; no automatic migration')
    reviewer = review.get('reviewer_id')
    if not isinstance(reviewer, str) or not re.fullmatch(r'[A-Za-z0-9_-]{2,40}', reviewer):
        raise ValueError('Reviewer identity is required: 2-40 letters, numbers, underscores or hyphens')
    if review.get('reviewer_kind') != 'human' or review.get('annotation_method') != 'manual':
        raise ValueError('Only explicitly human, manual annotations qualify as human reviews; machine labels are not gold')
    if review.get('independently_completed') is not True:
        raise ValueError('Independent human completion must be explicitly attested')
    if not timestamp(review.get('exported_at')):
        raise ValueError('Valid timezone-aware export timestamp required')
    if not isinstance(review.get('annotations'), list):
        raise ValueError('Annotations must be an array')
    known = {row['id']: row for row in manifest['items']}
    seen, result = set(), {}
    for row in review['annotations']:
        if not isinstance(row, dict):
            raise ValueError('Every annotation must be an object')
        item_id = row.get('id')
        if not isinstance(item_id, str) or item_id not in known or item_id in seen:
            raise ValueError('Unknown or duplicate item ID')
        seen.add(item_id)
        if row.get('reviewer_id') != reviewer:
            raise ValueError('Inconsistent reviewer identity')
        if row.get('text_sha256') != known[item_id]['text_sha256']:
            raise ValueError('Text snapshot mismatch')
        if row.get('rubric_version') != 'v2':
            raise ValueError('Per-item rubric mismatch')
        if not timestamp(row.get('completed_at')):
            raise ValueError('Valid timezone-aware completion timestamp required')
        if row.get('status') == 'skipped':
            if not nonempty(row.get('skip_reason'), 3):
                raise ValueError('Skip reason required')
            continue
        if row.get('status') != 'reviewed' or row.get('full_text_read') is not True:
            raise ValueError('Full-text review required')
        context = row.get('text_context')
        if (not isinstance(context, dict) or context.get('scope') != 'complete_frozen_text'
                or context.get('text_sha256') != known[item_id]['text_sha256']
                or context.get('external_context_used') not in (True, False)
                or type(context.get('external_context_used')) is not bool):
            raise ValueError('Exact frozen text context and explicit external-context disclosure required')
        if context['external_context_used'] and not nonempty(context.get('external_context_notes'), 10):
            raise ValueError('Disclose what external context was read and where')
        exposure = row.get('prior_exposure')
        if not isinstance(exposure, dict) or any(type(exposure.get(k)) is not bool for k in EXPOSURE):
            raise ValueError('Explicit model, legacy-label and other-reviewer exposure required')
        if any(exposure[k] for k in EXPOSURE) and not nonempty(exposure.get('notes'), 10):
            raise ValueError('Exposure notes required')
        if row.get('review_phase') not in PHASES or not nonempty(row.get('review_pass_id')):
            raise ValueError('Review phase and pass identity required')
        if row['review_phase'] in {'post_discussion_rereview', 'frozen_main'} and not nonempty(row.get('rubric_freeze_id')):
            raise ValueError('Record the agreed rubric freeze before the post-discussion or main pass')
        relevance, framing, label = row.get('relevance'), row.get('author_framing'), row.get('label')
        if relevance not in {'POLITICAL', 'NONPOLITICAL', 'UNCERTAIN'} or framing not in FRAMING or label not in LABELS:
            raise ValueError('Invalid relevance, author framing or label')
        if ((relevance == 'POLITICAL' and (framing == 'NOT_APPLICABLE' or label != framing))
                or (relevance == 'NONPOLITICAL' and (framing != 'NOT_APPLICABLE' or label != 'NONPOLITICAL'))
                or (relevance == 'UNCERTAIN' and (framing != 'UNCERTAIN' or label != 'UNCERTAIN'))):
            raise ValueError('Final label must be derived from relevance and author framing, never policy stance')
        if row.get('issue_policy_stance') not in POLICY or row.get('attribution') not in ATTRIBUTION:
            raise ValueError('Explicit policy-assessment status and attribution required')
        if relevance == 'NONPOLITICAL' and row['issue_policy_stance'] not in {'NOT_ASSESSED', 'NOT_APPLICABLE', 'NO_EXPLICIT_STANCE'}:
            raise ValueError('Nonpolitical material cannot carry a directional policy stance')
        if row.get('context_sufficiency') not in {'SUFFICIENT', 'INSUFFICIENT', 'UNCERTAIN'} or row.get('uncertainty_reason') not in UNCERTAINTY:
            raise ValueError('Context sufficiency and uncertainty reason required')
        if label == 'UNCERTAIN' and row['uncertainty_reason'] == 'NONE':
            raise ValueError('Uncertain judgments require an uncertainty reason')
        if label != 'UNCERTAIN' and row['uncertainty_reason'] != 'NONE':
            raise ValueError('Use NONE for a resolved primary label; explain residual ambiguity in rationale')
        if label in {'LEFT', 'CENTER', 'RIGHT'} and row['context_sufficiency'] != 'SUFFICIENT':
            raise ValueError('Resolved political author framing requires sufficient context')
        if row.get('confidence') not in {'low', 'medium', 'high'} or not nonempty(row.get('rationale'), 15):
            raise ValueError('Missing review evidence')
        validate_spans(row, known[item_id], snapshots)
        result[item_id] = row
    return result


def wilson_interval(successes, n):
    """95% Wilson binomial interval; descriptive, not an accuracy/release interval."""
    if not n:
        return None
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    middle = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0.0, middle - half), min(1.0, middle + half)]


def agreement(pairs, field):
    n = len(pairs)
    if not n:
        return {'n': 0, 'agree_n': 0, 'disagree_n': 0, 'agreement': None, 'agreement_ci95_wilson': None, 'cohens_kappa': None}
    a, b = Counter(x[field] for x, _ in pairs), Counter(y[field] for _, y in pairs)
    agree = sum(x[field] == y[field] for x, y in pairs)
    observed = agree / n
    chance = sum(a[k] * b[k] for k in set(a) | set(b)) / n ** 2
    return {'n': n, 'agree_n': agree, 'disagree_n': n - agree, 'agreement': observed,
            'agreement_ci95_wilson': wilson_interval(agree, n),
            'cohens_kappa': (observed - chance) / (1 - chance) if chance < 1 else None,
            'reviewer_a_counts': dict(a), 'reviewer_b_counts': dict(b)}


def per_axis(pairs):
    result = {}
    for field in AXES:
        eligible = pairs
        if field == 'author_framing':
            eligible = [(a, b) for a, b in pairs if a['relevance'] == b['relevance'] == 'POLITICAL']
        elif field == 'issue_policy_stance':
            eligible = [(a, b) for a, b in pairs if a[field] not in {'NOT_ASSESSED', 'NOT_APPLICABLE'} and b[field] not in {'NOT_ASSESSED', 'NOT_APPLICABLE'}]
        result[field] = {**agreement(eligible, field), 'excluded_n': len(pairs) - len(eligible)}
    return result


def blinded(row):
    return (not any(row['prior_exposure'][key] for key in EXPOSURE)
            and not row['text_context']['external_context_used']
            and row['review_phase'] != 'post_discussion_rereview')


def compare(first, second, manifest, snapshots=None):
    a, b = validate(first, manifest, snapshots), validate(second, manifest, snapshots)
    if first['reviewer_id'].casefold() == second['reviewer_id'].casefold():
        raise ValueError('Two distinct independent human reviewers required; repeat passes are not new reviewers')
    common = sorted(set(a) & set(b))
    pairs = [(a[k], b[k]) for k in common]
    items = {r['id']: r for r in manifest['items']}
    primary_axes = ('relevance', 'author_framing', 'issue_policy_stance', 'attribution', 'context_sufficiency', 'uncertainty_reason')
    disagreements = []
    for key in common:
        fields = [f for f in primary_axes if a[key][f] != b[key][f]]
        flags = []
        if a[key]['label'] == 'UNCERTAIN' or b[key]['label'] == 'UNCERTAIN':
            flags.append('primary_uncertainty')
        if a[key]['text_context']['external_context_used'] or b[key]['text_context']['external_context_used']:
            flags.append('external_context')
        if any(a[key]['prior_exposure'][f] or b[key]['prior_exposure'][f] for f in EXPOSURE):
            flags.append('prior_exposure')
        if any(validate_spans(row, items[key], snapshots)['verification'] == 'unverified_missing_snapshot' for row in (a[key], b[key])):
            flags.append('span_source_unverified')
        if a[key]['review_phase'] != b[key]['review_phase'] or a[key].get('rubric_freeze_id') != b[key].get('rubric_freeze_id'):
            flags.append('different_review_round_or_freeze')
        if a[key].get('span_status', 'NOT_ASSESSED') != b[key].get('span_status', 'NOT_ASSESSED') or a[key].get('evidence_spans', []) != b[key].get('evidence_spans', []):
            fields.append('evidence_spans')
        if fields or flags:
            disagreements.append({'id': key, 'kind': items[key]['kind'], 'disagreement_axes': fields,
                                  'review_flags': flags, 'reviewer_a': a[key], 'reviewer_b': b[key],
                                  'adjudicated_author_framing': None, 'adjudicated_relevance': None,
                                  'adjudicator_id': None, 'adjudication_rationale': None})
    same_round = [(x, y) for x, y in pairs if x['review_phase'] == y['review_phase'] and x.get('rubric_freeze_id') == y.get('rubric_freeze_id')]
    strictly_blinded = [(x, y) for x, y in same_round if blinded(x) and blinded(y)]
    axes = per_axis(pairs)
    return {
        'schema_version': 2, 'pilot_id': manifest['pilot_id'], 'rubric_version': 'v2',
        'purpose': 'human rubric-development agreement only; no model gold or accuracy',
        'reviewers': [first['reviewer_id'], second['reviewer_id']],
        'provenance_basis': 'self-reported human manual independent completion; not identity authentication',
        'completed': [len(a), len(b)], 'paired_n': len(common),
        'missing_or_skipped_ids': sorted(set(items) - set(common)),
        'per_axis': axes, 'label_agreement': axes['label'], 'relevance_agreement': axes['relevance'],
        'same_round': {'paired_n': len(same_round), 'per_axis': per_axis(same_round),
                       'span_agreement': span_agreement(same_round, items, snapshots)},
        'blinded_frozen_text_only': {'paired_n': len(strictly_blinded), 'per_axis': per_axis(strictly_blinded),
                                    'span_agreement': span_agreement(strictly_blinded, items, snapshots)},
        'slices': {kind: {'paired_n': sum(items[k]['kind'] == kind for k in common),
                          'per_axis': per_axis([(a[k], b[k]) for k in common if items[k]['kind'] == kind])}
                   for kind in ['historical_article', 'controlled_example']},
        'span_agreement': span_agreement(pairs, items, snapshots),
        'span_slices': {kind: span_agreement([(a[k], b[k]) for k in common if items[k]['kind'] == kind], items, snapshots) for kind in ['historical_article', 'controlled_example']},
        'disagreements': disagreements, 'gold_labels_approved': False,
        'limitations': [
            'Agreement measures consistency, not accuracy; no gold labels are created',
            'Raw agreement intervals are descriptive Wilson intervals, assuming independent items; clustered sources/events may widen uncertainty',
            'No kappa interval is reported; kappa is unstable or undefined with small/degenerate samples',
            'Reviewer identity and independence are self-attested, not externally verified',
            'All-paired diagnostics may include exposure/context differences; inspect same-round and blinded subsets',
            'Natural articles and synthetic controls must not be pooled into a real-world performance claim',
            'Pilot examples remain development material and cannot become an independent final test',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--second', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('pilot_manifest_v2.json'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--snapshots', type=Path, help='Pinned dataset data/jsons folder, required to verify historical span offsets')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    snapshots = {}
    if args.snapshots:
        for item in manifest['items']:
            if item.get('dataset_id'):
                path = args.snapshots / (str(item['dataset_id']) + '.json')
                if path.exists():
                    data = json.loads(path.read_text())
                    if str(data.get('ID')) != str(item['dataset_id']):
                        raise ValueError('Span source snapshot ID mismatch')
                    snapshots[item['id']] = data['content_original'].strip()
    result = compare(json.loads(args.first.read_text()), json.loads(args.second.read_text()), manifest, snapshots)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['disagreements', 'missing_or_skipped_ids']}, indent=2))


if __name__ == '__main__':
    main()
