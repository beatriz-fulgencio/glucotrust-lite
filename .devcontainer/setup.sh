#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python -m pip install --user -r requirements.txt
python -m pip install --user '.[dev]'
python -m pip check
