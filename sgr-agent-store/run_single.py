#!/usr/bin/env python3
"""
Run a single task without creating a full session.

Usage:
    python run_single.py soda_pack_optimizer
    python run_single.py hidden_cheap_gpu
    python run_single.py  # defaults to soda_pack_optimizer

Note: Tasks created this way are not linked to your account,
so they won't appear in the web UI session list.
You can view them directly via the URL printed.
"""
import sys
import os
import textwrap
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from erc3 import ERC3, TaskInfo
from store_agent import run_agent
from config import AgentConfig, default_config

# Get spec_id from command line or use default
spec_id = sys.argv[1] if len(sys.argv) > 1 else "soda_pack_optimizer"

# Use config
config = default_config
core = ERC3()

print(f"Creating task: {config.benchmark}/{spec_id}")
result = core.start_new_task(benchmark=config.benchmark, spec_id=spec_id)

print(f"Task ID: {result.task_id}")
print(f"URL: https://erc.timetoact-group.at/tasks/{result.task_id}")
print("=" * 60)

# Get task details to get the task text
task_detail = core.task_detail(result.task_id)
print(f"Task text: {task_detail.text}")
print("=" * 60)

# Create a TaskInfo-like object for compatibility with run_agent
# run_agent expects: task_id, spec_id, task_text
class SingleTask:
    def __init__(self, task_id: str, spec_id: str, task_text: str):
        self.task_id = task_id
        self.spec_id = spec_id
        self.task_text = task_text

task = SingleTask(
    task_id=result.task_id,
    spec_id=task_detail.spec,
    task_text=task_detail.text
)

# Log file path from config
LOG_FILE = f"{config.task_log_dir}/task_{spec_id}.log"
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
with open(LOG_FILE, "w") as f:
    f.write(f"Task: {result.task_id}\n")
    f.write(f"Spec: {spec_id}\n")
    f.write(f"Model: {config.model_id}\n")
    f.write(f"URL: https://erc.timetoact-group.at/tasks/{result.task_id}\n")
    f.write("=" * 60 + "\n\n")

print(f"Log file: {LOG_FILE}")
print("Starting agent...")
print("=" * 60)

try:
    run_agent(core, task, config, LOG_FILE)
except Exception as e:
    print(f"Error: {e}")

# Complete the task to trigger evaluation
# complete_task expects TaskInfo, so we reuse our task object
complete_result = core.complete_task(task)

print("=" * 60)
if complete_result.eval:
    print(f"SCORE: {complete_result.eval.score}")
    print(f"Evaluation:\n{textwrap.indent(complete_result.eval.logs, '  ')}")
else:
    print(f"Status: {complete_result.status}")
    print("No evaluation available")

print("=" * 60)
print(f"View task: https://erc.timetoact-group.at/tasks/{result.task_id}")
