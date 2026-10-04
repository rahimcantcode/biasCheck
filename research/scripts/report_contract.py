"""Fail-closed checks for supplied evaluation provenance; not human authentication."""
MODEL_FIELDS = ('weights_sha256', 'config_sha256', 'tokenizer_sha256',
                'aggregation', 'max_length', 'stride', 'id2label')


def require_unique_examples(report):
    rows = report.get('predictions')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Nonempty prediction list required')
    seen_ids, seen_hashes = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Prediction rows must be objects')
        id, fingerprint = row.get('id'), row.get('text_sha256')
        if not isinstance(id, str) or not id.strip():
            raise ValueError('Nonblank example ID required')
        if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(c not in '0123456789abcdefABCDEF' for c in fingerprint):
            raise ValueError('Valid text SHA-256 required')
        fingerprint = fingerprint.lower()
        if id in seen_ids or fingerprint in seen_hashes:
            raise ValueError('Duplicate example ID or text SHA-256')
        seen_ids.add(id)
        seen_hashes.add(fingerprint)


def require_human_provenance(report):
    provenance = report.get('annotation_provenance')
    if not isinstance(provenance, dict) or provenance.get('human_reviewed') is not True:
        raise ValueError('Explicit boolean human-reviewed confirmation required')
    reference = provenance.get('reference')
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError('Nonblank human annotation reference required')


def require_matching_reports(test, validation):
    for report in (test, validation):
        require_human_provenance(report)
    if not test.get('mode') or test.get('mode') != validation.get('mode'):
        raise ValueError('Test and validation analysis modes must match')
    for field in MODEL_FIELDS:
        first = test.get('model', {}).get(field)
        second = validation.get('model', {}).get(field)
        if first is None or second is None or first != second:
            raise ValueError('Test/validation model mismatch: ' + field)
