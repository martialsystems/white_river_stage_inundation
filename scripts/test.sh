#!/usr/bin/env bash
# Run the suite with the project venv. Stock macOS python3 has no rasterio.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -x .venv/bin/python ]]; then
  echo "missing .venv. python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 2
fi
exec .venv/bin/python -m pytest tests -q "$@"
