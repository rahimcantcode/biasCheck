"""Human exact-span extension v1: codepoint offsets in the frozen source text."""
import hashlib

SPAN_STATUSES = {'NOT_ASSESSED', 'NO_DIRECTIONAL_SPANS', 'ANNOTATED'}


def resolve_text(item, snapshots=None):
    text = item.get('text')
    if text is None and snapshots is not None:
        text = snapshots.get(item['id'])
    if text is None:
        return None
    if not isinstance(text, str) or hashlib.sha256(text.encode('utf-8')).hexdigest() != item['text_sha256']:
        raise ValueError('Span source snapshot hash mismatch')
    return text


def validate_spans(row, item, snapshots=None):
    # Older v2 exports are not silently promoted to span-reviewed records.
    status = row.get('span_status', 'NOT_ASSESSED')
    spans = row.get('evidence_spans', [])
    if status not in SPAN_STATUSES or not isinstance(spans, list):
        raise ValueError('Invalid span status or evidence spans array')
    if status != 'NOT_ASSESSED' or spans:
        if type(row.get('span_protocol_version')) is not int or row['span_protocol_version'] != 1:
            raise ValueError('Span protocol version 1 required')
    if (status == 'ANNOTATED') != bool(spans):
        raise ValueError('ANNOTATED requires spans; no-span/unassessed records must have none')
    text = resolve_text(item, snapshots)
    previous_end = -1
    for span in spans:
        if not isinstance(span, dict):
            raise ValueError('Span must be an object')
        start, end = span.get('start'), span.get('end')
        if type(start) is not int or type(end) is not int or not 0 <= start < end:
            raise ValueError('Span requires nonempty Unicode codepoint offsets')
        if start < previous_end:
            raise ValueError('Spans must be sorted and nonoverlapping; duplicate spans are not allowed')
        previous_end = end
        if span.get('source_text_sha256') != item['text_sha256']:
            raise ValueError('Span source snapshot hash mismatch')
        if span.get('direction') not in {'LEFT', 'RIGHT'} or span.get('attribution') not in {'AUTHOR', 'QUOTED', 'UNKNOWN'}:
            raise ValueError('Span direction and attribution required')
        if not isinstance(span.get('text'), str) or not span['text'].strip() or len(span['text']) != end - start:
            raise ValueError('Span text length must match Unicode codepoint offsets')
        if text is not None and (end > len(text) or text[start:end] != span['text']):
            raise ValueError('Span text does not exactly match the frozen source offsets')
    if status == 'NOT_ASSESSED':
        verification = 'not_assessed'
    elif text is None:
        verification = 'unverified_missing_snapshot'
    else:
        verification = 'verified_exact_source'
    return {'status': status, 'verification': verification, 'span_n': len(spans),
            'eligible_for_human_adjudication': verification == 'verified_exact_source',
            'gold_qualified': False}


def span_agreement(pairs, items, snapshots=None):
    """Symmetric exact-span diagnostics. Neither reviewer is a reference/gold label."""
    eligible, a_n, b_n, matches = 0, 0, 0, 0
    missing, unassessed, empty_both = [], [], 0
    verification = []
    for a, b in pairs:
        item = items[a['id']]
        av, bv = validate_spans(a, item, snapshots), validate_spans(b, item, snapshots)
        verification.append({'id': a['id'], 'reviewer_a': av, 'reviewer_b': bv})
        if 'not_assessed' in {av['verification'], bv['verification']}:
            unassessed.append(a['id'])
            continue
        if av['verification'] != 'verified_exact_source' or bv['verification'] != 'verified_exact_source':
            missing.append(a['id'])
            continue
        eligible += 1
        key = lambda s: (s['start'], s['end'], s['direction'], s['attribution'])
        aa, bb = {key(s) for s in a.get('evidence_spans', [])}, {key(s) for s in b.get('evidence_spans', [])}
        a_n += len(aa)
        b_n += len(bb)
        matches += len(aa & bb)
        empty_both += not aa and not bb
    return {'paired_items': len(pairs), 'verified_assessed_pairs': eligible,
            'excluded_missing_snapshot_ids': missing, 'excluded_unassessed_ids': unassessed,
            'reviewer_a_span_n': a_n, 'reviewer_b_span_n': b_n, 'exact_matched_span_n': matches,
            'reviewer_a_exact_match_fraction': matches / a_n if a_n else None,
            'reviewer_b_exact_match_fraction': matches / b_n if b_n else None,
            'symmetric_exact_span_f1': 2 * matches / (a_n + b_n) if a_n + b_n else None,
            'both_no_directional_spans_n': empty_both, 'verification': verification,
            'gold_qualified': False,
            'definition': 'Exact codepoint boundaries + LEFT/RIGHT direction + attribution; symmetric human agreement, neither reviewer is gold'}
