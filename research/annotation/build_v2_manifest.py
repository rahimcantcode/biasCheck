"""Derive a new rubric version without altering v1 text, IDs, selection, or labels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    original = (ROOT / 'pilot_manifest.json').read_bytes()
    manifest = json.loads(original)
    assert manifest['schema_version'] == 1
    manifest.update({
        'schema_version': 2,
        'pilot_id': 'biascheck-rubric-pilot-20261002-v2',
        'rubric_version': 'v2',
        'parent_pilot_id': manifest['pilot_id'],
        'parent_manifest_sha256': hashlib.sha256(original).hexdigest(),
        'context_policy': 'complete_frozen_text_only',
        'primary_construct': 'political_author_framing',
        'human_reviewed': False,
    })
    (ROOT / 'pilot_manifest_v2.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    build()
