"""Session log parser - extract tasks and steps from session logs"""

import re
import json
from typing import List, Dict, Any, Optional

# Lines starting with these markers are ignored
IGNORED_LINE_PREFIXES = [
    "[dumb_model]",
]

# Compact mode: replace large lists with element count
# Format: {function_substring: [path, to, list]}
COMPACT_LIST_RULES = {
    "All_Products": ["result", "products"],
}


def _should_ignore_line(line: str) -> bool:
    """Check if line should be ignored based on markers."""
    stripped = line.strip()
    for prefix in IGNORED_LINE_PREFIXES:
        if stripped.startswith(prefix):
            return True
    return False


def _apply_compact_rules(step: Dict[str, Any]) -> None:
    """Apply compact rules to step in-place, replacing large lists with counts."""
    function_name = step.get("function", "")

    for substring, path in COMPACT_LIST_RULES.items():
        if substring in function_name:
            # Navigate to the list using path
            obj = step
            for key in path[:-1]:
                if isinstance(obj, dict) and key in obj:
                    obj = obj[key]
                else:
                    obj = None
                    break

            # Replace the list with count
            if obj is not None and isinstance(obj, dict):
                last_key = path[-1]
                if last_key in obj and isinstance(obj[last_key], list):
                    count = len(obj[last_key])
                    obj[last_key] = [{"elements": count}]


def parse_session_log(log_text: str, compact: bool = False) -> Dict[str, Any]:
    """
    Parse session log text into dict with tasks.

    Args:
        log_text: Raw session log text
        compact: If True, replace large lists with element counts per COMPACT_LIST_RULES

    Returns:
        Dict with:
        - prompt_hashes: Dict with body and guidelines hashes (or None if not found)
        - tasks: List of task dicts, each containing:
            - id: str
            - code: str
            - text: str
            - score: float
            - pass: str
            - stats: {duration, tokens: {prompt, completion}}
            - steps: List[Dict] with keys:
                - current_state: str
                - plan: list
                - task_completed: bool
                - function: str
                - args: dict
                - result: dict
                - stats: {duration, tokens: {prompt, completion}}
    """
    tasks = []
    current_task = None
    current_step = None
    prompt_hashes = None

    lines = log_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip ignored lines
        if _should_ignore_line(line):
            i += 1
            continue

        # Parse prompt_hashes (at beginning of log)
        if line.startswith("prompt_hashes:"):
            hashes_json = line[14:].strip()
            try:
                prompt_hashes = json.loads(hashes_json)
            except json.JSONDecodeError:
                prompt_hashes = None
            i += 1
            continue

        # Match TASK header: "TASK: tsk-xxx (code)"
        task_match = re.match(r'^TASK:\s+(\S+)\s+\(([^)]+)\)', line)
        if task_match:
            # Save previous task if exists
            if current_task is not None:
                if current_step is not None:
                    if compact:
                        _apply_compact_rules(current_step)
                    current_task["steps"].append(current_step)
                    current_step = None
                tasks.append(current_task)

            current_task = {
                "id": task_match.group(1),
                "code": task_match.group(2),
                "text": None,
                "score": None,
                "pass": None,
                "stats": {"duration": None, "tokens": {"prompt": None, "completion": None}},
                "steps": [],
            }
            i += 1
            continue

        # Match TEXT line (follows TASK)
        if current_task and line.startswith("TEXT:"):
            current_task["text"] = line[5:].strip()
            i += 1
            continue

        # Match step header: "--- step_N ---"
        step_match = re.match(r'^---\s+step_\d+\s+---', line)
        if step_match and current_task is not None:
            # Save previous step
            if current_step is not None:
                if compact:
                    _apply_compact_rules(current_step)
                current_task["steps"].append(current_step)

            current_step = {
                "stats": {"duration": None, "tokens": {"prompt": None, "completion": None}},
                "current_state": None,
                "plan": None,
                "task_completed": None,
                "function": None,
                "args": None,
                "result": None,
            }
            i += 1
            continue

        # Parse step fields
        if current_step is not None:
            # time: "time: 1.7s elapsed, step took 1.7s"
            time_match = re.match(r'^time:.*step took ([\d.]+)s', line)
            if time_match:
                current_step["stats"]["duration"] = float(time_match.group(1))
                i += 1
                continue

            # tokens: "tokens: step=2062 (completion=62), task=2062, session=2062"
            tokens_match = re.match(r'^tokens:\s+step=(\d+)\s+\(completion=(\d+)\)', line)
            if tokens_match:
                step_total = int(tokens_match.group(1))
                completion = int(tokens_match.group(2))
                current_step["stats"]["tokens"]["completion"] = completion
                current_step["stats"]["tokens"]["prompt"] = step_total - completion
                i += 1
                continue

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

        # Parse task-level fields (after steps)
        if current_task is not None:
            # SCORE: 1.0
            score_match = re.match(r'^SCORE:\s+([\d.]+)', line)
            if score_match:
                current_task["score"] = float(score_match.group(1))
                i += 1
                continue

            # PASS: ...
            if line.startswith("PASS:"):
                current_task["pass"] = line[5:].strip()
                i += 1
                continue

            # Task stats: 17.9s, 20057 tokens (prompt: 19212, completion: 845)
            stats_match = re.match(r'^Task stats:\s+([\d.]+)s,\s+\d+\s+tokens\s+\(prompt:\s+(\d+),\s+completion:\s+(\d+)\)', line)
            if stats_match:
                current_task["stats"]["duration"] = float(stats_match.group(1))
                current_task["stats"]["tokens"]["prompt"] = int(stats_match.group(2))
                current_task["stats"]["tokens"]["completion"] = int(stats_match.group(3))
                i += 1
                continue

        i += 1

    # Save last task and step
    if current_task is not None:
        if current_step is not None:
            if compact:
                _apply_compact_rules(current_step)
            current_task["steps"].append(current_step)
        tasks.append(current_task)

    return {"prompt_hashes": prompt_hashes, "tasks": tasks}


def get_task_summary(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary of a task.

    Returns:
        Dict with id, code, text, step_count, functions_used
    """
    return {
        "id": task["id"],
        "code": task["code"],
        "text": task["text"],
        "step_count": len(task["steps"]),
        "functions_used": [s["function"] for s in task["steps"]]
    }
