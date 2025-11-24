import json
import subprocess
import textwrap
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from store_agent import run_agent, session_tokens, write_session_log
from config import default_config
from erc3 import ERC3

def get_git_commit() -> str:
    """Get current git commit hash (short form)"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""

def log_event(message: str):
    """Print timestamped event to stdout"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{ts}: {message}")

config = default_config
core = ERC3()

# Track session start time
session_start_time = time.time()
session_start_timestamp = datetime.now().isoformat()


# Start session with metadata
res = core.start_session(
    benchmark=config.benchmark,
    workspace=config.workspace,
    name=config.session_name,
    architecture=config.architecture,
)

log_event(f"Session started: {res.session_id}")

# Log file path from config
LOG_FILE = config.session_log
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
with open(LOG_FILE, "w") as f:
    f.write(f"Session: {res.session_id}\n")
    f.write(f"Model: {config.model_id}\n")
    f.write(f"URL: https://erc.timetoact-group.at/sessions/{res.session_id}\n")
    f.write("="*60 + "\n\n")

status = core.session_status(res.session_id)

# Track scores for session summary
task_scores = []

for task in status.tasks:
    # Skip tasks not in task_codes (if filter is set)
    if config.task_codes and task.spec_id not in config.task_codes:
        core.start_task(task)
        core.complete_task(task)
        continue

    # start the task
    log_event(f"Task started: {task.spec_id}")
    core.start_task(task)
    try:
        run_agent(core, task, config, LOG_FILE)
    except Exception as e:
        print(e)
    result = core.complete_task(task)
    if result.eval:
        score = result.eval.score
        task_scores.append(score)
        log_event(f"Task completed: {task.spec_id} | Score: {score}")
        # Write score to log file
        write_session_log(LOG_FILE, f"SCORE: {score}\n", f"{result.eval.logs}\n\n")

core.submit_session(res.session_id)
log_event(f"Session completed: {res.session_id} | Score: {sum(task_scores)/len(task_scores):.1%}")

# Calculate total time and save to sessions history
total_time_sec = time.time() - session_start_time

# Read session log
session_log_content = ""
if Path(LOG_FILE).exists():
    with open(LOG_FILE, "r") as f:
        session_log_content = f.read()

# Calculate session score
session_score = sum(task_scores) / len(task_scores) if task_scores else 0.0

# Build session record
session_record = {
    "start_timestamp": session_start_timestamp,
    "session_id": res.session_id,
    "commit": get_git_commit(),
    "session_score": round(session_score, 3),
    "session_tasks_quantity": len(task_scores),
    "config": config.model_dump(),
    "token_statistics": session_tokens,
    "total_time_sec": round(total_time_sec, 1),
    "session_log": session_log_content,
}

# Append to sessions history file (with retry on concurrent access)
SESSIONS_HISTORY_FILE = Path(config.sessions_history)
for attempt in range(3):
    try:
        history = []
        if SESSIONS_HISTORY_FILE.exists():
            with open(SESSIONS_HISTORY_FILE, "r") as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []

        history.append(session_record)

        with open(SESSIONS_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        break  # Success
    except (IOError, OSError) as e:
        if attempt < 2:
            time.sleep(1)
        else:
            print(f"Warning: Could not save session history after 3 attempts: {e}")

