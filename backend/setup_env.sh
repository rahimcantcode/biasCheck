#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: --index-url https://pypi.org/simple pip==26.2
.venv/bin/python -m pip install --only-binary=:all: 'torch==2.13.0+cpu' --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install --only-binary=:all: --index-url https://pypi.org/simple -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -c "import torch; assert torch.__version__ == '2.13.0+cpu' and torch.version.cuda is None, torch.__version__"
