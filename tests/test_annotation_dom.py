"""Node DOM/event fixture, not a real-browser or visual-layout assertion."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from research.annotation.compare_reviews import validate

ROOT = Path(__file__).resolve().parents[1]


def test_reviewer_dom_provenance_save_import_export():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable; DOM fixture not run')
    result = subprocess.run(
        [node, 'research/annotation/test_reviewer_dom.cjs'],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output['checks'] == 24
    manifest = json.loads((ROOT / 'research/annotation/pilot_manifest_v2.json').read_text())
    # The actual exported event-fixture payload must also satisfy the Python validator.
    assert len(validate(output['exported'], manifest)) == 1
