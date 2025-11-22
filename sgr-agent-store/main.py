import textwrap
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from store_agent import run_agent
from erc3 import ERC3

client = OpenAI()
core = ERC3()
MODEL_ID = "gpt-4o"

# Filter tasks by spec_id. If empty, run all tasks.
# Example: TASK_CODES = ["soda_pack_optimizer", "pet_store_best_coupon"]
TASK_CODES = []

# Start session with metadata
res = core.start_session(
    benchmark="store",
    workspace="my",
    name="Simple SGR Agent",
    architecture="NextStep SGR Agent with OpenAI")

# Create session log file
# LOG_FILE = f"session_{res.session_id}.log"
LOG_FILE = f"session.log"
with open(LOG_FILE, "w") as f:
    f.write(f"Session: {res.session_id}\n")
    f.write(f"Model: {MODEL_ID}\n")
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
        run_agent(MODEL_ID, core, task, LOG_FILE)
    except Exception as e:
        print(e)
    result = core.complete_task(task)
    if result.eval:
        explain = textwrap.indent(result.eval.logs, "  ")
        print(f"\nSCORE: {result.eval.score}\n{explain}\n")

core.submit_session(res.session_id)











