#!/usr/bin/env python3
"""
Task Manager for Opus-Sonnet collaboration.

Facilitates task handoff and tracking between models through the filesystem.
"""

import json
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    PLANNING = "planning"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"


class TaskManager:
    """Manages task flow between Opus and Sonnet models."""

    def __init__(self, base_dir: str = None):
        """Initialize task manager with base directory."""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.handoff_dir = self.base_dir / "handoff"
        self.experiments_dir = self.base_dir / "experiments"

        # Ensure directories exist
        self.handoff_dir.mkdir(exist_ok=True, parents=True)
        (self.handoff_dir / "opus_to_sonnet").mkdir(exist_ok=True)
        (self.handoff_dir / "sonnet_to_opus").mkdir(exist_ok=True)
        (self.handoff_dir / "shared").mkdir(exist_ok=True)

    def create_task(
        self,
        description: str,
        task_type: str = "implementation",
        priority: Priority = Priority.MEDIUM,
        context_files: List[str] = None
    ) -> str:
        """
        Create a new task for Opus planning.

        Args:
            description: What needs to be done
            task_type: Type of task (planning, implementation, review)
            priority: Task priority
            context_files: List of files to include as context

        Returns:
            Task ID
        """
        task_id = f"task_{datetime.now():%Y%m%d_%H%M%S}"

        task = {
            "id": task_id,
            "type": task_type,
            "priority": priority.value,
            "description": description,
            "created": datetime.now().isoformat(),
            "status": TaskStatus.PLANNING.value,
            "context_files": context_files or []
        }

        # Save task
        task_file = self.handoff_dir / "opus_to_sonnet" / "current_task.json"
        task_file.write_text(json.dumps(task, indent=2))

        print(f"✓ Task created: {task_id}")
        print(f"  Priority: {priority.value}")
        print(f"  Type: {task_type}")

        if context_files:
            print(f"  Context: {', '.join(context_files)}")

        print("\n📋 Next step for Opus:")
        print(f"Read handoff/opus_to_sonnet/current_task.json")
        print(f"Create detailed implementation plan")

        return task_id

    def prepare_for_sonnet(self) -> None:
        """Prepare context and instructions for Sonnet."""
        files_to_read = []

        # Check for opus plan
        opus_plan = self.handoff_dir / "opus_to_sonnet" / "implementation_plan.md"
        if opus_plan.exists():
            files_to_read.append(str(opus_plan.relative_to(self.base_dir)))

        # Check for shared context
        shared_files = [
            "architecture.md",
            "interfaces.json",
            "decisions_log.md"
        ]

        for file in shared_files:
            path = self.handoff_dir / "shared" / file
            if path.exists():
                files_to_read.append(str(path.relative_to(self.base_dir)))

        if not files_to_read:
            print("⚠️ No files found for Sonnet. Has Opus created the plan?")
            return

        print("📋 Context for Sonnet:")
        print(f"Files to read:")
        for f in files_to_read:
            print(f"  - {f}")

        print("\nInstructions for Sonnet:")
        print("1. Read the files above")
        print("2. Implement according to the plan")
        print("3. Write status updates to handoff/sonnet_to_opus/status.md")
        print("4. Log any questions to handoff/sonnet_to_opus/questions.json")

    def check_status(self) -> None:
        """Check current task status from both models."""
        print("📊 Current Status\n")

        # Check Opus task
        task_file = self.handoff_dir / "opus_to_sonnet" / "current_task.json"
        if task_file.exists():
            task = json.loads(task_file.read_text())
            print(f"Active Task: {task['id']}")
            print(f"  Status: {task['status']}")
            print(f"  Priority: {task['priority']}")
            print(f"  Created: {task['created']}")
            print()

        # Check Sonnet status
        status_file = self.handoff_dir / "sonnet_to_opus" / "status.md"
        if status_file.exists():
            print("Sonnet Status:")
            status_content = status_file.read_text()
            # Show first 5 lines
            lines = status_content.split('\n')[:5]
            for line in lines:
                print(f"  {line}")
            if len(status_content.split('\n')) > 5:
                print("  ...")
            print()

        # Check for questions
        questions_file = self.handoff_dir / "sonnet_to_opus" / "questions.json"
        if questions_file.exists():
            questions = json.loads(questions_file.read_text())
            if questions.get("pending"):
                print(f"⚠️ Pending Questions: {len(questions['pending'])}")
                for q in questions['pending'][:3]:
                    print(f"  - {q.get('question', 'N/A')[:60]}...")
                print()

        # Check for escalations
        self.check_escalations()

    def check_escalations(self) -> None:
        """Check for any escalations requiring user attention."""
        escalation_files = list((self.handoff_dir / "sonnet_to_opus").glob("escalation_*.json"))

        if not escalation_files:
            return

        print("🔴 ESCALATIONS REQUIRING ATTENTION:")

        for file in escalation_files:
            try:
                data = json.loads(file.read_text())
                priority = data.get("priority", "unknown")

                icon = "🔴" if priority == "critical" else "🟡"
                print(f"\n{icon} {data.get('issue', 'Unknown issue')}")
                print(f"   Priority: {priority}")

                if "options" in data:
                    print("   Options:")
                    for opt in data["options"]:
                        print(f"     {opt['id']}: {opt.get('solution', 'N/A')}")

                if "recommendation" in data:
                    print(f"   Recommended: {data['recommendation']}")

                if "deadline" in data:
                    print(f"   Deadline: {data['deadline']}")

            except Exception as e:
                print(f"   Error reading {file.name}: {e}")

    def create_escalation(
        self,
        issue: str,
        options: List[Dict[str, str]],
        priority: Priority = Priority.HIGH,
        recommendation: str = None,
        deadline: str = None
    ) -> None:
        """
        Create an escalation for user attention.

        Args:
            issue: Description of the problem
            options: List of solution options
            priority: Escalation priority
            recommendation: Recommended option
            deadline: When decision is needed
        """
        escalation = {
            "issue": issue,
            "priority": priority.value,
            "options": options,
            "created": datetime.now().isoformat()
        }

        if recommendation:
            escalation["recommendation"] = recommendation
        if deadline:
            escalation["deadline"] = deadline

        filename = f"escalation_{priority.value}_{datetime.now():%Y%m%d_%H%M%S}.json"
        file_path = self.handoff_dir / "sonnet_to_opus" / filename
        file_path.write_text(json.dumps(escalation, indent=2))

        print(f"🔴 Escalation created: {filename}")
        print(f"   Priority: {priority.value}")
        print(f"   Issue: {issue[:60]}...")

    def record_decision(
        self,
        decision: str,
        context: str,
        options_considered: List[str],
        rationale: str,
        impact: str = None,
        reversible: bool = True
    ) -> None:
        """
        Record a decision in the decision log.

        Args:
            decision: What was decided
            context: Why this decision was needed
            options_considered: What alternatives were evaluated
            rationale: Why this option was chosen
            impact: What changes as a result
            reversible: Whether the decision can be easily reversed
        """
        log_file = self.handoff_dir / "shared" / "decisions_log.md"

        # Read existing content
        if log_file.exists():
            content = log_file.read_text()
        else:
            content = "# Decision Log\n\n"

        # Add new decision
        entry = f"""
## {datetime.now():%Y-%m-%d}: {decision}

**Context**: {context}

**Options Considered**:
"""
        for i, opt in enumerate(options_considered, 1):
            entry += f"{i}. {opt}\n"

        entry += f"""
**Decision**: {decision}
**Rationale**: {rationale}
"""

        if impact:
            entry += f"**Impact**: {impact}\n"

        entry += f"**Reversible**: {'Yes' if reversible else 'No'}\n"
        entry += "\n---\n"

        # Insert after the header
        lines = content.split('\n')
        if len(lines) > 2:
            lines.insert(2, entry)
            content = '\n'.join(lines)
        else:
            content += entry

        log_file.write_text(content)
        print(f"✓ Decision recorded in decisions_log.md")

    def archive_task(self, task_id: str) -> None:
        """Archive a completed task."""
        # Move task files to completed
        task_file = self.handoff_dir / "opus_to_sonnet" / "current_task.json"
        if task_file.exists():
            task = json.loads(task_file.read_text())
            task["completed"] = datetime.now().isoformat()
            task["status"] = TaskStatus.COMPLETED.value

            archive_file = self.handoff_dir / "completed" / f"{task_id}.json"
            archive_file.parent.mkdir(exist_ok=True)
            archive_file.write_text(json.dumps(task, indent=2))

            # Clear current task
            task_file.unlink()
            print(f"✓ Task {task_id} archived")

    def summary(self) -> None:
        """Print a summary of the current state."""
        print("=" * 50)
        print("TASK MANAGER SUMMARY")
        print("=" * 50)

        self.check_status()

        # Count files
        opus_files = list((self.handoff_dir / "opus_to_sonnet").glob("*"))
        sonnet_files = list((self.handoff_dir / "sonnet_to_opus").glob("*"))
        shared_files = list((self.handoff_dir / "shared").glob("*"))

        print("📁 File Counts:")
        print(f"  Opus → Sonnet: {len(opus_files)} files")
        print(f"  Sonnet → Opus: {len(sonnet_files)} files")
        print(f"  Shared: {len(shared_files)} files")

        print("\n💡 Quick Commands:")
        print("  tm.create_task('description')  # Create new task")
        print("  tm.prepare_for_sonnet()        # Prepare Sonnet context")
        print("  tm.check_status()              # Check current status")
        print("  tm.check_escalations()         # Check escalations")

    def load_plan(self) -> Dict:
        """Load the implementation plan."""
        plan_file = self.base_dir / "implementation_plan.json"
        if not plan_file.exists():
            print(f"⚠️ Plan file not found: {plan_file}")
            return {}

        return json.loads(plan_file.read_text())

    def get_next_task(self, plan: Optional[Dict] = None) -> Optional[Dict]:
        """
        Find the next available task from the plan.

        A task is available if:
        - Its status is 'pending'
        - All its dependencies are 'completed'

        Returns:
            Next available task or None if no tasks available
        """
        if plan is None:
            plan = self.load_plan()

        for phase_name, phase in plan.items():
            if phase.get("status") == "completed":
                continue

            for task in phase.get("tasks", []):
                if task.get("status") != "pending":
                    continue

                # Check dependencies
                deps_met = True
                for dep_id in task.get("dependencies", []):
                    if not self._is_task_completed(plan, dep_id):
                        deps_met = False
                        break

                if deps_met:
                    return task

        return None

    def _is_task_completed(self, plan: Dict, task_id: str) -> bool:
        """Check if a task is completed in the plan."""
        for phase in plan.values():
            for task in phase.get("tasks", []):
                if task.get("id") == task_id:
                    return task.get("status") == "completed"
        return False

    def create_task_from_plan(self, task: Dict) -> None:
        """
        Create current_task.json from a plan task.

        Args:
            task: Task dictionary from the plan
        """
        current_task = {
            "id": task["id"],
            "name": task["name"],
            "branch_name": task.get("branch_name", f"task-{task['id']}"),
            "deliverables": task["deliverables"],
            "acceptance_criteria": task["acceptance_criteria"],
            "technical_notes": task.get("technical_notes", ""),
            "estimated_hours": task.get("estimated_hours", 0),
            "test_before_complete": True,
            "escalation_rules": "See handoff/opus_to_sonnet/escalation_rules.md",
            "created": datetime.now().isoformat(),
            "status": "ready"
        }

        task_file = self.handoff_dir / "opus_to_sonnet" / "current_task.json"
        task_file.write_text(json.dumps(current_task, indent=2))

        print(f"✓ Task {task['id']} prepared for implementation")
        print(f"  Name: {task['name']}")
        print(f"  Branch: {current_task['branch_name']}")
        print(f"  Deliverables: {len(task['deliverables'])} files")

    def update_plan_status(self, task_id: str, status: str) -> None:
        """
        Update a task's status in the implementation plan.

        Args:
            task_id: Task ID to update
            status: New status (pending, in_progress, completed)
        """
        plan = self.load_plan()

        # Find and update the task
        updated = False
        for phase_name, phase in plan.items():
            for task in phase.get("tasks", []):
                if task.get("id") == task_id:
                    task["status"] = status
                    if status == "completed":
                        task["completed_at"] = datetime.now().isoformat()
                    elif status == "in_progress":
                        task["started_at"] = datetime.now().isoformat()
                    updated = True
                    break
            if updated:
                break

        if updated:
            # Check if phase is complete
            self._update_phase_status(plan, phase_name)

            # Save updated plan
            plan_file = self.base_dir / "implementation_plan.json"
            plan_file.write_text(json.dumps(plan, indent=2))
            print(f"✓ Task {task_id} status updated to: {status}")
        else:
            print(f"⚠️ Task {task_id} not found in plan")

    def _update_phase_status(self, plan: Dict, phase_name: str) -> None:
        """Update phase status based on task statuses."""
        phase = plan.get(phase_name, {})
        tasks = phase.get("tasks", [])

        if not tasks:
            return

        all_completed = all(t.get("status") == "completed" for t in tasks)
        any_in_progress = any(t.get("status") == "in_progress" for t in tasks)
        any_completed = any(t.get("status") == "completed" for t in tasks)

        if all_completed:
            phase["status"] = "completed"
        elif any_in_progress or any_completed:
            phase["status"] = "in_progress"
        else:
            phase["status"] = "pending"

    def get_project_status(self) -> Dict:
        """
        Get the current project status summary.

        Returns:
            Dictionary with completed, in_progress, and pending task lists
        """
        plan = self.load_plan()

        completed = []
        in_progress = []
        pending = []
        blocked = []

        for phase_name, phase in plan.items():
            for task in phase.get("tasks", []):
                task_id = task.get("id")
                status = task.get("status", "pending")

                if status == "completed":
                    completed.append(task_id)
                elif status == "in_progress":
                    in_progress.append(task_id)
                elif status == "pending":
                    # Check if dependencies are met
                    deps_met = all(
                        self._is_task_completed(plan, dep)
                        for dep in task.get("dependencies", [])
                    )
                    if deps_met:
                        pending.append(task_id)
                    else:
                        blocked.append(task_id)

        return {
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "blocked": blocked
        }

    def get_plan_progress(self) -> None:
        """Display the current progress of the implementation plan."""
        plan = self.load_plan()

        print("\n📊 Implementation Plan Progress\n")

        for phase_name, phase in plan.items():
            tasks = phase.get("tasks", [])
            completed = sum(1 for t in tasks if t.get("status") == "completed")
            in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
            total = len(tasks)

            status_icon = {
                "completed": "✅",
                "in_progress": "🔄",
                "pending": "⏳",
                "planned": "📋"
            }.get(phase.get("status", "pending"), "❓")

            print(f"{status_icon} {phase.get('name', phase_name)}")
            print(f"   Progress: {completed}/{total} tasks completed")

            if in_progress > 0:
                print(f"   In Progress: {in_progress} task(s)")

            # Show next available task in this phase
            for task in tasks:
                if task.get("status") == "pending":
                    deps_met = all(
                        self._is_task_completed(plan, dep)
                        for dep in task.get("dependencies", [])
                    )
                    if deps_met:
                        print(f"   Next: {task['id']} - {task['name']}")
                        break

            print()


def main():
    """CLI interface for task manager."""
    import sys

    tm = TaskManager()

    if len(sys.argv) < 2:
        tm.summary()
        return

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 3:
            print("Usage: task_manager.py create 'task description'")
            return
        description = ' '.join(sys.argv[2:])
        tm.create_task(description)

    elif command == "status":
        tm.check_status()

    elif command == "prepare":
        tm.prepare_for_sonnet()

    elif command == "escalations":
        tm.check_escalations()

    elif command == "summary":
        tm.summary()

    elif command == "plan":
        tm.get_plan_progress()

    elif command == "next":
        plan = tm.load_plan()
        next_task = tm.get_next_task(plan)
        if next_task:
            print(f"Next available task: {next_task['id']} - {next_task['name']}")
            print("Run 'task_manager.py start' to begin this task")
        else:
            print("No tasks available (all completed or dependencies not met)")

    elif command == "start":
        plan = tm.load_plan()
        next_task = tm.get_next_task(plan)
        if next_task:
            tm.create_task_from_plan(next_task)
            tm.update_plan_status(next_task['id'], 'in_progress')
        else:
            print("No tasks available to start")

    elif command == "complete":
        if len(sys.argv) < 3:
            print("Usage: task_manager.py complete <task_id>")
            return
        task_id = sys.argv[2]
        tm.update_plan_status(task_id, 'completed')

    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, status, prepare, escalations, summary, plan, next, start, complete")


if __name__ == "__main__":
    main()