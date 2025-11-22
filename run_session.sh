#!/bin/bash
# Run full session with all tasks
# Usage: ./run_session.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
cd sgr-agent-store
python main.py "$@"
