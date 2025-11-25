"""Hash mapping management for prompt tracking"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List


DEFAULT_HASHES_FILE = Path(__file__).parent / "data" / "hashes.dict"


def compose_guidelines(guidelines: List[str]) -> str:
    """
    Compose guidelines list into numbered text block.

    Args:
        guidelines: List of guideline strings

    Returns:
        String with numbered guidelines joined by newlines
    """
    numbered_guidelines = [
        f"{i}. {line}" for i, line in enumerate(guidelines)
    ]
    return "\n".join(numbered_guidelines)


def compute_prompt_hashes(system_prompt: str, system_prompt_guidelines: List[str]) -> Dict[str, Any]:
    """
    Compute md5 hashes for prompt components.

    Args:
        system_prompt: The prompt template text
        system_prompt_guidelines: List of guideline strings

    Returns:
        Dict with structure: {
            'body': hash of system_prompt,
            'guidelines': {
                'combined': hash of composed guidelines,
                'lines': [hash of each guideline line]
            }
        }
    """
    def md5_hash(text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    # Hash the prompt body (template)
    body_hash = md5_hash(system_prompt)

    # Hash each guideline line
    line_hashes = [md5_hash(line) for line in system_prompt_guidelines]

    # Hash the composed guidelines
    composed = compose_guidelines(system_prompt_guidelines)
    combined_hash = md5_hash(composed)

    return {
        'body': body_hash,
        'guidelines': {
            'combined': combined_hash,
            'lines': line_hashes
        }
    }


def load_hash_dict(hashes_file: Path = None) -> Dict[str, str]:
    """
    Load hash -> text mappings from file.

    Args:
        hashes_file: Path to hashes.dict file. Defaults to analysis/data/hashes.dict

    Returns:
        Dict mapping hash strings to original text
    """
    file_path = hashes_file or DEFAULT_HASHES_FILE

    if not file_path.exists():
        return {}

    with open(file_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_hash_dict(hash_dict: Dict[str, str], hashes_file: Path = None):
    """
    Save hash -> text mappings to file.

    Loads existing mappings, merges with new ones, and saves back.
    Thread-safe with retry logic for concurrent access.

    Args:
        hash_dict: Dict mapping hash strings to original text
        hashes_file: Path to hashes.dict file. Defaults to analysis/data/hashes.dict
    """
    from common import safe_read_modify_write_json

    file_path = hashes_file or DEFAULT_HASHES_FILE

    def merge_hashes(existing):
        if existing is None:
            existing = {}
        existing.update(hash_dict)
        return existing

    safe_read_modify_write_json(file_path, merge_hashes, default={})


def record_prompt_hashes(hashes_data: Dict[str, Any], prompt_body: str, guidelines: list) -> Dict[str, str]:
    """
    Build hash -> text mappings from prompt hashes and save them.

    Args:
        hashes_data: Output from compute_prompt_hashes()
        prompt_body: The system_prompt template text
        guidelines: List of guideline strings

    Returns:
        Dict of hash -> text mappings that were recorded
    """
    mappings = {}

    # Map body hash
    mappings[hashes_data['body']] = prompt_body

    # Map combined guidelines hash
    composed = compose_guidelines(guidelines)
    mappings[hashes_data['guidelines']['combined']] = composed

    # Map each guideline line hash
    for i, (line_hash, line_text) in enumerate(zip(hashes_data['guidelines']['lines'], guidelines)):
        mappings[line_hash] = line_text

    # Save to file
    save_hash_dict(mappings)

    return mappings
