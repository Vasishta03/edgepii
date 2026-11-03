#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
exec .venv/bin/python -m edgepii.gui --host 0.0.0.0 --port "${EDGEPII_PORT:-7860}" "$@"
