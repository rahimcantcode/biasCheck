#!/usr/bin/env bash

set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade --force-reinstall -r requirements.txt
pip install --force-reinstall --no-deps tokenizers==0.22.2

python - <<'PY'
from pathlib import Path

dependency_table = Path(".venv/lib/python3.11/site-packages/transformers/dependency_versions_table.py")
content = dependency_table.read_text()
content = content.replace(
    '"tokenizers": "tokenizers>=0.19,<0.20",',
    '"tokenizers": "tokenizers>=0.19",',
)
dependency_table.write_text(content)
print("Patched transformers dependency check for standalone tokenizers runtime.")
PY
