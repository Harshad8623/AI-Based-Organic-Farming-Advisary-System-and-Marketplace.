#!/usr/bin/env bash
set -euo pipefail
cd /workspace/organic-farming-platform
python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), "Use the pinned Python 3.12 runtime"'
export PIP_CACHE_DIR=/workspace/.cache/pip
if [ ! -x venv/bin/python ]; then
  python3 -m venv venv
fi
venv/bin/python -m pip install --disable-pip-version-check pip==26.2.1
venv/bin/python -m pip install --disable-pip-version-check -r requirements-dev.txt -c requirements-lock.txt
venv/bin/python -m pip check
venv/bin/python -c 'from app import create_app; create_app()'
