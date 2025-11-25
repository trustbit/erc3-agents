"""File operation utilities for concurrent access safety"""

import json
import time
from pathlib import Path
from typing import Any, Callable


def safe_json_write(
    file_path: Path | str,
    data: Any,
    max_attempts: int = 3,
    delay: float = 0.5
) -> bool:
    """
    Safely write JSON data to file with retry on concurrent access errors.

    Args:
        file_path: Path to JSON file
        data: Data to serialize as JSON
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between retries

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    for attempt in range(max_attempts):
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"Warning: Could not write to {file_path} after {max_attempts} attempts: {e}")
                return False
    return False


def safe_file_append(
    file_path: Path | str,
    content: str,
    max_attempts: int = 3,
    delay: float = 0.1
) -> bool:
    """
    Safely append content to file with retry on concurrent access errors.

    Args:
        file_path: Path to file
        content: Content to append
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between retries

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    for attempt in range(max_attempts):
        try:
            with open(file_path, "a") as f:
                f.write(content)
            return True
        except (IOError, OSError) as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"Warning: Could not append to {file_path} after {max_attempts} attempts: {e}")
                return False
    return False


def safe_read_modify_write_json(
    file_path: Path | str,
    modifier: Callable[[Any], Any],
    default: Any = None,
    max_attempts: int = 3,
    delay: float = 0.5
) -> bool:
    """
    Safely read-modify-write JSON file with retry.

    Args:
        file_path: Path to JSON file
        modifier: Function that takes current data and returns modified data
        default: Default value if file doesn't exist
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between retries

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    for attempt in range(max_attempts):
        try:
            # Read
            if file_path.exists():
                with open(file_path, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = default
            else:
                data = default

            # Modify
            data = modifier(data)

            # Write
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except (IOError, OSError) as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"Warning: Could not update {file_path} after {max_attempts} attempts: {e}")
                return False
    return False
