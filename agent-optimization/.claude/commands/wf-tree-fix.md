# Update and fix project structure documentation

## Find Structure Documentation

Look for files documenting project structure:
```bash
echo "=== Files with structure documentation ==="
grep -l "Project Structure\|Directory Structure\|Structure" --include="*.md" -r . 2>/dev/null | grep -v ".git"
```

## Generate Current Structure

```bash
echo "=== Actual Project Structure ==="
tree -L 3 -I '__pycache__|*.pyc|.git' . > /tmp/current_structure.txt
cat /tmp/current_structure.txt
```

Or without tree command:
```bash
find . -type d -name ".git" -prune -o -type d -name "__pycache__" -prune -o -type f -print | \
    grep -v ".pyc" | \
    sort | \
    sed 's|^\./||' | \
    awk -F/ '{
        depth = NF-1
        for (i=0; i<depth; i++) printf "  "
        print $NF
    }'
```

## Compare with Documented Structure

Key file to update: `handoff/opus_to_sonnet/coding_standards.md`

Check if these directories exist as documented:
```python
import os

documented_structure = {
    "agent-optimization/config": ["__init__.py", "loader.py", "schema.py", "validator.py"],
    "agent-optimization/analysis": ["sprt.py", "enhanced_parser.py"],
    "agent-optimization/analysis/core": ["filters.py", "aggregators.py"],
    "agent-optimization/cli": [],
    "tests/test_config": ["test_loader.py", "test_schema.py"],
    "tests/test_analysis": ["test_sprt.py"],
    "examples": [],
    "handoff/opus_to_sonnet": ["START_HERE.md", "current_task.json", "coding_standards.md", "escalation_rules.md"],
    "handoff/sonnet_to_opus": [],
    "handoff/shared": ["architecture.md", "decisions_log.md"],
    "handoff/user_to_opus": ["START_PROJECT.md", "REVIEW_WORKFLOW.md", "review_template.md"],
    "docs": ["PROJECT.md", "COLLABORATION.md"]
}

discrepancies = []

for dir_path, expected_files in documented_structure.items():
    if not os.path.exists(dir_path):
        discrepancies.append(f"Missing directory: {dir_path}")
    else:
        for file in expected_files:
            file_path = os.path.join(dir_path, file)
            if not os.path.exists(file_path):
                discrepancies.append(f"Missing file: {file_path}")

# Check for undocumented items
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache']]

    rel_root = os.path.relpath(root, ".")
    if rel_root == ".":
        continue

    if rel_root not in documented_structure:
        if any(important in root for important in ['agent-optimization', 'handoff', 'tests', 'docs']):
            discrepancies.append(f"Undocumented directory: {rel_root}")

if discrepancies:
    print("⚠️ DISCREPANCIES FOUND:")
    for d in discrepancies:
        print(f"  - {d}")
else:
    print("✅ Structure matches documentation")
```

## Update Documentation

If discrepancies found, update `handoff/opus_to_sonnet/coding_standards.md`:

```python
# Generate updated structure section
updated_structure = """## Project Structure

```
agent-optimization/
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── loader.py          # Config loading logic
│   ├── schema.py          # Pydantic models
│   └── validator.py       # Validation logic
├── analysis/
│   ├── core/              # Core analysis tools
│   │   ├── filters.py
│   │   └── aggregators.py
│   ├── sprt.py           # Statistical testing
│   └── enhanced_parser.py # Session parsing
├── cli/                   # Command-line interface
├── experiment_runner.py   # Main experiment orchestration
└── task_manager.py        # Task management utilities

tests/                     # Mirror source structure
├── test_config/
│   ├── test_loader.py
│   └── test_schema.py
└── test_analysis/
    └── test_sprt.py

examples/                  # Working examples
├── configs/              # Example configurations
├── run_experiment.py     # Example experiment
└── filter_demo.py        # Filter usage demo

handoff/                   # Model communication
├── opus_to_sonnet/       # Opus → Sonnet (tasks, standards)
│   ├── START_HERE.md     # Sonnet onboarding
│   ├── current_task.json # Active task specification
│   ├── coding_standards.md
│   └── escalation_rules.md
├── sonnet_to_opus/       # Sonnet → Opus (reports)
│   └── (empty - will contain implementation_log.md, escalation.json)
├── shared/               # Common information
│   ├── architecture.md  # System design
│   └── decisions_log.md # Architecture decisions
└── user_to_opus/         # User → Opus (instructions)
    ├── START_PROJECT.md  # Opus onboarding
    ├── REVIEW_WORKFLOW.md # Review process
    └── review_template.md # Review checklist

docs/                      # Project documentation
├── PROJECT.md            # Project overview
└── COLLABORATION.md      # Role definitions

.claude/commands/         # Workflow automation
├── wf-agent-status.md   # Check agent states
├── wf-coder-refresh.md  # Refresh Sonnet
├── wf-arch-refresh.md   # Refresh Opus
└── ...                  # Other workflow commands
```
"""

# Update the file
# Read current content, replace structure section, write back
```

## Additional Checks

1. **Check for orphaned files**:
```bash
# Files not in any documentation
find . -name "*.py" -o -name "*.md" | while read file; do
    if ! grep -q "$(basename $file)" handoff/opus_to_sonnet/coding_standards.md; then
        echo "Undocumented: $file"
    fi
done
```

2. **Check for README files**:
```bash
# Directories that might need README
for dir in agent-optimization tests examples handoff docs; do
    if [ ! -f "$dir/README.md" ]; then
        echo "Consider adding README to $dir/"
    fi
done
```

## Report

Summary:
1. Documentation files checked
2. Discrepancies found and fixed
3. Structure now accurate
4. Any directories needing README files
5. Validation complete