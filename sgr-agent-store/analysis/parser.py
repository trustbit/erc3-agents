"""Session log parser - extract tasks and steps from session logs"""

import re
import json
from typing import List, Dict, Any, Optional

# Lines starting with these markers are ignored
IGNORED_LINE_PREFIXES = [
    "[dumb_model]",
]


def _should_ignore_line(line: str) -> bool:
    """Check if line should be ignored based on markers."""
    stripped = line.strip()
    for prefix in IGNORED_LINE_PREFIXES:
        if stripped.startswith(prefix):
            return True
    return False


def parse_session_log(log_text: str) -> List[Dict[str, Any]]:
    """
    Parse session log text into list of tasks with steps.

    Args:
        log_text: Raw session log text

    Returns:
        List of task dicts, each containing:
        - task_id: str
        - task_code: str
        - task_text: str
        - steps: List[Dict] with keys:
            - current_state: str
            - plan: list
            - task_completed: bool
            - function: str
            - args: dict
            - result: dict
    """
    tasks = []
    current_task = None
    current_step = None

    lines = log_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip ignored lines
        if _should_ignore_line(line):
            i += 1
            continue

        # Match TASK header: "TASK: tsk-xxx (code)"
        task_match = re.match(r'^TASK:\s+(\S+)\s+\(([^)]+)\)', line)
        if task_match:
            # Save previous task if exists
            if current_task is not None:
                if current_step is not None:
                    current_task["steps"].append(current_step)
                    current_step = None
                tasks.append(current_task)

            current_task = {
                "task_id": task_match.group(1),
                "task_code": task_match.group(2),
                "task_text": "",
                "steps": []
            }
            i += 1
            continue

        # Match TEXT line (follows TASK)
        if current_task and line.startswith("TEXT:"):
            current_task["task_text"] = line[5:].strip()
            i += 1
            continue

        # Match step header: "--- step_N ---"
        step_match = re.match(r'^---\s+step_\d+\s+---', line)
        if step_match and current_task is not None:
            # Save previous step
            if current_step is not None:
                current_task["steps"].append(current_step)

            current_step = {
                "current_state": "",
                "plan": [],
                "task_completed": False,
                "function": "",
                "args": {},
                "result": {}
            }
            i += 1
            continue

        # Parse step fields
        if current_step is not None:
            # current_state:
            if line.startswith("current_state:"):
                current_step["current_state"] = line[14:].strip()
                i += 1
                continue

            # plan:
            if line.startswith("plan:"):
                plan_str = line[5:].strip()
                try:
                    current_step["plan"] = eval(plan_str)  # Safe for list literals
                except:
                    current_step["plan"] = [plan_str]
                i += 1
                continue

            # task_completed:
            if line.startswith("task_completed:"):
                value = line[15:].strip()
                current_step["task_completed"] = value == "True"
                i += 1
                continue

            # function:
            if line.startswith("function:"):
                current_step["function"] = line[9:].strip()
                i += 1
                continue

            # args: (indented with 2 spaces)
            if line.startswith("  args:"):
                args_str = line[7:].strip()
                try:
                    current_step["args"] = json.loads(args_str)
                except json.JSONDecodeError:
                    current_step["args"] = {"raw": args_str}
                i += 1
                continue

            # result: (indented with 2 spaces)
            if line.startswith("  result:"):
                result_str = line[9:].strip()
                try:
                    current_step["result"] = json.loads(result_str)
                except json.JSONDecodeError:
                    current_step["result"] = {"raw": result_str}
                i += 1
                continue

        i += 1

    # Save last task and step
    if current_task is not None:
        if current_step is not None:
            current_task["steps"].append(current_step)
        tasks.append(current_task)

    return tasks


def get_task_summary(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary of a task.

    Returns:
        Dict with task_id, task_code, task_text, step_count, functions_used
    """
    return {
        "task_id": task["task_id"],
        "task_code": task["task_code"],
        "task_text": task["task_text"],
        "step_count": len(task["steps"]),
        "functions_used": [s["function"] for s in task["steps"]]
    }
