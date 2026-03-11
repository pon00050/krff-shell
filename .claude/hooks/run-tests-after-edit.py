#!/usr/bin/env python3
"""PostToolUse hook: run pytest after .py file edits or writes.

Batch mode
----------
When making multiple sequential edits to interdependent files, running the
full test suite after every single edit wastes ~60s per edit and can surface
misleading failures (e.g. a renamed constant breaks tests until all usages
are updated).

To suppress per-edit runs and run once at the end instead:

    # Before starting a batch of edits:
    touch .batch-edits          # or: New-Item .batch-edits -ItemType File (PowerShell)

    # Make all edits freely — hook skips tests while flag file exists.

    # When all edits are done:
    rm .batch-edits             # or: Remove-Item .batch-edits (PowerShell)
    python -m pytest tests/ -x -q   # run once manually to confirm clean state

.batch-edits is gitignored. Never commit it.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    data = json.load(sys.stdin)
    file_path = data.get("tool_input", {}).get("file_path", "")
except (json.JSONDecodeError, AttributeError):
    sys.exit(0)

if not file_path.endswith(".py"):
    sys.exit(0)

# Skip test files to avoid infinite loops
if "test_" in file_path or file_path.endswith("_test.py"):
    sys.exit(0)

# ── Batch mode check ────────────────────────────────────────────────────────
# If .batch-edits exists in the project root, skip this run.
# Delete the file and run tests manually when the batch is complete.
project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
batch_flag = project_root / ".batch-edits"
if batch_flag.exists():
    print(
        f"[hook] batch mode active — skipping tests after editing {Path(file_path).name}. "
        f"Delete {batch_flag} and run pytest manually when done.",
        file=sys.stderr,
    )
    sys.exit(0)

# ── Normal mode: run full suite ─────────────────────────────────────────────
result = subprocess.run(
    ["uv", "run", "python", "-m", "pytest", "tests/", "-x", "-q"],
    capture_output=True,
    text=True,
    timeout=120,
)

if result.returncode != 0:
    print(f"TESTS FAILED after editing {file_path}", file=sys.stderr)
    output = result.stdout
    print(output[-500:] if len(output) > 500 else output, file=sys.stderr)
    sys.exit(2)

sys.exit(0)
