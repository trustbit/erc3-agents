"""View task details from ERC3 API

Usage:
    python scripts/view_task.py <task_id>
    python scripts/view_task.py tsk-42Jj1GfXt3ogFS1CxJQxWP
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from erc3 import ERC3


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/view_task.py <task_id>")
        print("Example: python scripts/view_task.py tsk-42Jj1GfXt3ogFS1CxJQxWP")
        sys.exit(1)

    task_id = sys.argv[1]

    api = ERC3()
    detail = api.task_detail(task_id)

    print("=" * 60)
    print(f"Task ID: {detail.task_id}")
    print(f"Spec ID: {detail.spec_id}")
    print(f"Status: {detail.status}")
    print("=" * 60)
    print(f"\nTask Text:\n{detail.task_text}")

    if detail.eval:
        print(f"\n{'=' * 60}")
        print(f"Evaluation:")
        print(f"  Score: {detail.eval.score}")
        if detail.eval.logs:
            print(f"  Logs:\n{detail.eval.logs}")

    if detail.logs:
        print(f"\n{'=' * 60}")
        print(f"Execution Logs ({len(detail.logs)} entries):")
        print("=" * 60)

        for i, log in enumerate(detail.logs):
            print(f"\n--- Log {i + 1} ---")
            # Convert log to dict for pretty printing
            log_dict = log.model_dump(exclude_none=True, exclude_unset=True)
            print(json.dumps(log_dict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
