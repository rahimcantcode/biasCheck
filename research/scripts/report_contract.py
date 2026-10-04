"""Fail-closed checks for supplied evaluation provenance; not human authentication."""
MODEL_FIELDS = ('weights_sha256', 'config_sha256', 'tokenizer_sha256',
                'aggregation', 'max_length', 'stride', 'id2label')


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
