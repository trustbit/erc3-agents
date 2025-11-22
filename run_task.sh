#!/bin/bash
# Run a single task from sgr-agent-store
# Usage: ./run_task.sh [spec_id]
# Example: ./run_task.sh soda_pack_optimizer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source venv/bin/activate
cd sgr-agent-store

python run_single.py "$@"
