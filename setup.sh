#!/bin/bash
# fullstack-agent setup — find a working Python, then run the setup script.
# Phase 3 bootstrap (Mac/Linux).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$HERE/setup.py" "$@"
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run python "$HERE/setup.py" "$@"
fi
echo "No working Python found. Install Python 3 first (macOS ships it; Linux usually has it), then re-run setup."
exit 1
