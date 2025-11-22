import textwrap
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from store_agent import run_agent
from config import default_config
from erc3 import ERC3

# Log files go to repository root (parent of sgr-agent-store)
REPO_ROOT = Path(__file__).parent.parent

config = default_config
core = ERC3()

# Filter tasks by spec_id. If empty, run all tasks.
# Example: TASK_CODES = ["soda_pack_optimizer", "pet_store_best_coupon"]
TASK_CODES = []

# Start session with metadata
res = core.start_session(
    benchmark=config.benchmark,
    workspace=config.workspace,
    name=config.session_name,
    architecture=config.architecture,
)

print(f"Session: {res.session_id}")
print(f"URL: https://erc.timetoact-group.at/sessions/{res.session_id}")

# Create session log file in repository root
LOG_FILE = str(REPO_ROOT / "session.log")
with open(LOG_FILE, "w") as f:
    f.write(f"Session: {res.session_id}\n")
    f.write(f"Model: {config.model_id}\n")
    f.write(f"URL: https://erc.timetoact-group.at/sessions/{res.session_id}\n")
    f.write("="*60 + "\n\n")

status = core.session_status(res.session_id)
print(f"Session has {len(status.tasks)} tasks")
print(f"Log file: {LOG_FILE}")

for task in status.tasks:
    print("="*40)
    print(f"Starting Task: {task.task_id} ({task.spec_id}): {task.task_text}")

    # Skip tasks not in TASK_CODES (if filter is set)
    if TASK_CODES and task.spec_id not in TASK_CODES:
        print("SKIPPED (not in TASK_CODES)")
        core.start_task(task)
        core.complete_task(task)
        continue

    # start the task
    core.start_task(task)
    try:
        run_agent(core, task, config, LOG_FILE)
    except Exception as e:
        print(e)
    result = core.complete_task(task)
    if result.eval:
        explain = textwrap.indent(result.eval.logs, "  ")
        print(f"\nSCORE: {result.eval.score}\n{explain}\n")

core.submit_session(res.session_id)
print(f"\nSession submitted: https://erc.timetoact-group.at/sessions/{res.session_id}")
