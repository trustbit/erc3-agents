"""Session history statistics and analysis"""

import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

from config import default_config
from .parser import parse_session_log


def load_sessions(path: str = None) -> List[Dict[str, Any]]:
    """
    Load all sessions from history file.

    Args:
        path: Path to sessions history file. Defaults to config.sessions_history.

    Returns:
        List of session records (dicts).
    """
    file_path = Path(path) if path else Path(default_config.sessions_history)

    if not file_path.exists():
        return []

    with open(file_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def get_sessions(
    index: Union[int, slice, None] = None,
    path: str = None
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Get session(s) from history with Python-like indexing.

    Supports:
        - get_sessions()        → all sessions
        - get_sessions(0)       → first session
        - get_sessions(-1)      → last session
        - get_sessions(-3)      → third from end
        - get_sessions(slice(0, 5))      → first 5 sessions
        - get_sessions(slice(-3, None))  → last 3 sessions
        - get_sessions(slice(None, None, 2))  → every second session

    Args:
        index: Integer index, slice object, or None for all.
        path: Path to sessions history file.

    Returns:
        Single session dict (if int index) or list of sessions.

    Examples:
        >>> get_sessions()           # all
        >>> get_sessions(0)          # first
        >>> get_sessions(-1)         # last
        >>> get_sessions(slice(-5, None))  # last 5
    """
    sessions = load_sessions(path)

    if index is None:
        return sessions

    if isinstance(index, int):
        return sessions[index]

    if isinstance(index, slice):
        return sessions[index]

    raise TypeError(f"index must be int, slice, or None, got {type(index).__name__}")


def get_session_logs(
    index: Union[int, slice, None] = None,
    path: str = None,
    compact: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract session_id, commit, and session_log from sessions.

    Args:
        index: Python-like index (int, slice, or None for all).
        path: Path to sessions history file.
        compact: If True, replace large lists with element counts.

    Returns:
        List of dicts with keys: session_id, commit, session_log
    """
    sessions = get_sessions(index, path)

    # Normalize to list
    if isinstance(sessions, dict):
        sessions = [sessions]

    result = []
    for s in sessions:
        raw_log = s.get("session_log", "")
        result.append({
            "session_id": s.get("session_id"),
            "commit": s.get("commit"),
            "session_log": parse_session_log(raw_log, compact=compact) if raw_log else {"tasks": []},
        })
    return result


def get_task_across_sessions(
    task_codes: List[str],
    index: Union[int, slice, None] = None,
    path: str = None,
    compact: bool = False
) -> List[Dict[str, Any]]:
    """
    Get specific tasks from each session in the specified range.

    Useful for analyzing how particular tasks were solved across sessions.
    Returns sessions with only the requested tasks in session_log.

    Args:
        task_codes: List of task codes to extract (e.g., ["gpu_race", "pet_store_best_coupon"]).
        index: Python-like index (int, slice, or None for all).
        path: Path to sessions history file.
        compact: If True, replace large lists with element counts.

    Returns:
        List of session dicts, each containing only the requested tasks.
        Sessions without any matching tasks are omitted.

    Examples:
        >>> get_task_across_sessions(["gpu_race"], slice(-10, None))
        >>> get_task_across_sessions(["gpu_race", "pet_store_best_coupon"], compact=True)
    """
    sessions = get_sessions(index, path)

    # Normalize to list
    if isinstance(sessions, dict):
        sessions = [sessions]

    task_codes_set = set(task_codes)

    result = []
    for s in sessions:
        raw_log = s.get("session_log", "")
        if not raw_log:
            continue

        parsed = parse_session_log(raw_log, compact=compact)
        tasks = parsed.get("tasks", [])

        # Find matching tasks
        matching_tasks = [t for t in tasks if t.get("code") in task_codes_set]

        if matching_tasks:
            result.append({
                "session_id": s.get("session_id"),
                "commit": s.get("commit"),
                "session_log": {"tasks": matching_tasks},
            })

    return result
