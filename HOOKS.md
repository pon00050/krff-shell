# Privacy Enforcement Hooks — Implementation Reference

This document describes the deterministic guardrails that prevent private files
from being accidentally committed to this public repository.

---

## Table of Contents

1. [Defense-in-Depth Architecture](#defense-in-depth-architecture)
2. [Layer 1: `.gitignore`](#layer-1-gitignore)
3. [Layer 2: Claude Code PreToolUse Hook](#layer-2-claude-code-pretooluse-hook)
4. [Layer 3: Git Pre-Commit Hook](#layer-3-git-pre-commit-hook)
5. [How It Works End-to-End](#how-it-works-end-to-end)
6. [Setup for New Contributors](#setup-for-new-contributors)
7. [Testing the Hooks](#testing-the-hooks)
8. [Maintenance](#maintenance)

---

## Defense-in-Depth Architecture

Three independent layers protect the private file boundary. Each layer catches
different failure modes:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Commit Attempt                              │
│                                                                 │
│  Layer 1: .gitignore                                            │
│  ├─ Prevents `git add .` and `git add -A` from staging         │
│  ├─ Does NOT prevent `git add -f <file>` (force flag)           │
│  └─ Does NOT prevent `git add <file>` if file was once tracked  │
│                                                                 │
│  Layer 2: Claude Code PreToolUse Hook                           │
│  ├─ Intercepts ALL Bash commands before execution               │
│  ├─ Blocks `git add` if command references a private path       │
│  ├─ Deterministic — cannot be overridden by LLM reasoning       │
│  └─ Only applies to Claude Code sessions (not manual git)       │
│                                                                 │
│  Layer 3: Git Pre-Commit Hook                                   │
│  ├─ Runs on every `git commit` (by anyone)                      │
│  ├─ Inspects staged files via `git diff --cached --name-only`   │
│  ├─ Blocks the commit if any staged file matches a private path │
│  └─ Universal safety net — catches all bypass methods           │
└─────────────────────────────────────────────────────────────────┘
```

| Scenario | Layer 1 | Layer 2 | Layer 3 |
|---|:---:|:---:|:---:|
| `git add .` | Blocked | — | — |
| `git add -A` | Blocked | — | — |
| Claude runs `git add KNOWN_ISSUES.md` | Bypassed | **Blocked** | Blocked |
| Claude runs `git add -f KNOWN_ISSUES.md` | Bypassed | **Blocked** | Blocked |
| Human runs `git add -f KNOWN_ISSUES.md` | Bypassed | N/A | **Blocked** |
| Human runs `git add -f ... && git commit --no-verify` | Bypassed | N/A | Bypassed |

> **Note:** `git commit --no-verify` skips all git hooks. This is the only way
> to bypass all three layers and requires explicit, deliberate action.

---

## Layer 1: `.gitignore`

Standard git mechanism. The relevant entries in `.gitignore`:

```gitignore
# Private — local only
00_Reference/
KNOWN_ISSUES.md
CHANGELOG.md
PRODUCT_VISION.md
03_Analysis/company_dives/
.claude/CLAUDE.md
PHASE_1_5_PLAN.md
```

**Scope:** Prevents unintentional staging via wildcard commands (`git add .`,
`git add -A`). Does not prevent explicit `git add <file>` or `git add -f`.

---

## Layer 2: Claude Code PreToolUse Hook

### Overview

Claude Code supports [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) —
shell commands that execute at specific points in the agent lifecycle. A
**PreToolUse** hook runs *before* a tool is executed and can block it by exiting
with code 2.

We register a PreToolUse hook on the `Bash` tool that inspects every shell
command Claude is about to run. If the command is a `git add` that references
a private path, the hook blocks execution before it happens.

### File: `.claude/settings.json`

This is the **project-level** Claude Code settings file. It is committed to the
repository, so every contributor who uses Claude Code gets the hook automatically.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard-private-files.py\""
          }
        ]
      }
    ]
  }
}
```

**Key fields:**

| Field | Value | Purpose |
|---|---|---|
| `matcher` | `"Bash"` | Only intercept Bash tool invocations (not Read, Write, etc.) |
| `type` | `"command"` | Run a shell command as the hook |
| `command` | `python "...guard-private-files.py"` | The hook script to execute |
| `$CLAUDE_PROJECT_DIR` | (auto-resolved) | Points to the project root at runtime |

### File: `.claude/hooks/guard-private-files.py`

The hook script. Written in Python (not bash + jq) because `jq` is not
guaranteed to be available on all development environments.

```python
#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block git-add of private files.

Reads tool invocation JSON from stdin. If the Bash command is a `git add`
that references any private path, exits with code 2 to block the action.
"""
import json
import sys
import re

PRIVATE_PATTERNS = [
    "KNOWN_ISSUES.md",
    "CHANGELOG.md",
    "PRODUCT_VISION.md",
    "company_dives",
    "00_Reference",
]

def main():
    try:
        data = json.load(sys.stdin)
        command = data.get("tool_input", {}).get("command", "")
    except (json.JSONDecodeError, AttributeError):
        sys.exit(0)

    # Only check git add commands
    if not re.match(r"\s*git\s+add", command):
        sys.exit(0)

    for pattern in PRIVATE_PATTERNS:
        if pattern in command:
            print(
                f"BLOCKED: '{pattern}' is a private file/directory and must not "
                f"be staged for commit. See CLAUDE.md privacy rules.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### How the PreToolUse hook processes input

Claude Code sends a JSON object to the hook's stdin with this structure:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git add KNOWN_ISSUES.md",
    "description": "Stage file for commit"
  }
}
```

The hook script:

1. **Parses JSON** from stdin → extracts `tool_input.command`
2. **Regex check** — if the command does not match `^\s*git\s+add`, exits 0
   (allow). This ensures non-git commands are never delayed.
3. **Pattern scan** — checks if the command string contains any of the 5
   private patterns (substring match)
4. **Decision:**
   - Match found → print explanation to stderr, exit with **code 2** (block)
   - No match → exit with **code 0** (allow)

### Exit code semantics

| Exit Code | Meaning | Effect |
|---|---|---|
| 0 | Allow | Command executes normally |
| 2 | Block | Command is **prevented from executing**; stderr message shown to user |
| Other non-zero | Error | Hook is treated as failed; behavior depends on Claude Code version |

---

## Layer 3: Git Pre-Commit Hook

### Overview

A standard [git hook](https://git-scm.com/docs/githooks#_pre_commit) that runs
automatically before every `git commit`. It inspects the staged file list and
aborts the commit if any file matches a private path pattern.

This layer is **independent of Claude Code** — it protects against manual
mistakes by any contributor using any git client.

### File: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Pre-commit hook: block commits containing private files.
# These files are gitignored and local-only. If they appear in staging,
# something bypassed .gitignore (e.g., git add -f).

PRIVATE_PATTERNS=(
  "KNOWN_ISSUES.md"
  "CHANGELOG.md"
  "PRODUCT_VISION.md"
  "03_Analysis/company_dives/"
  "00_Reference/"
)

STAGED=$(git diff --cached --name-only)

for pattern in "${PRIVATE_PATTERNS[@]}"; do
  if echo "$STAGED" | grep -q "$pattern"; then
    echo "ERROR: Attempted to commit private file matching '$pattern'."
    echo "These files are local-only. Remove from staging: git reset HEAD <file>"
    exit 1
  fi
done

exit 0
```

### How it works

1. **Trigger:** Git calls this script automatically before creating a commit
2. **Inspection:** `git diff --cached --name-only` lists all staged file paths
3. **Pattern matching:** Each staged path is checked against the 5 private
   patterns using `grep` substring matching
4. **Decision:**
   - Match found → print error with remediation instructions, exit 1 (abort
     commit)
   - No match → exit 0 (allow commit)

### Important limitation

This file lives in `.git/hooks/`, which is **not tracked by git**. It exists
only on the local machine where it was created. New contributors must set it up
manually (see [Setup for New Contributors](#setup-for-new-contributors)).

---

## How It Works End-to-End

### Scenario A: Claude Code session — normal workflow

```
User: "commit the pipeline changes"

Claude: git add 02_Pipeline/pipeline.py
  → PreToolUse hook fires
  → Parses command: "git add 02_Pipeline/pipeline.py"
  → Matches "git add" regex: YES
  → Contains private pattern? NO
  → Exit 0 (ALLOW)
  → Command executes successfully

Claude: git commit -m "fix: update pipeline stage order"
  → Pre-commit hook fires
  → Staged files: 02_Pipeline/pipeline.py
  → Matches private pattern? NO
  → Exit 0 (ALLOW)
  → Commit succeeds
```

### Scenario B: Claude Code session — accidental private file staging

```
User: "commit everything"

Claude: git add KNOWN_ISSUES.md
  → PreToolUse hook fires
  → Parses command: "git add KNOWN_ISSUES.md"
  → Matches "git add" regex: YES
  → Contains "KNOWN_ISSUES.md"? YES
  → stderr: "BLOCKED: 'KNOWN_ISSUES.md' is a private file..."
  → Exit 2 (BLOCK)
  → Command NEVER executes
```

### Scenario C: Manual force-add by contributor

```
$ git add -f KNOWN_ISSUES.md    # Bypasses .gitignore — file is staged
$ git commit -m "oops"
  → Pre-commit hook fires
  → Staged files: KNOWN_ISSUES.md
  → Matches "KNOWN_ISSUES.md"? YES
  → "ERROR: Attempted to commit private file matching 'KNOWN_ISSUES.md'."
  → Exit 1 (ABORT)
  → Commit rejected

$ git reset HEAD KNOWN_ISSUES.md    # Remediation
```

---

## Setup for New Contributors

### Automatic (Claude Code hook)

The Claude Code hook is configured in `.claude/settings.json`, which is
committed to the repository. Any contributor who uses Claude Code in this
project gets the hook automatically — **no setup required**.

### Manual (Git pre-commit hook)

The git pre-commit hook must be installed manually. Run this from the project
root:

```bash
cp docs/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

> **Future improvement:** Adopt a pre-commit framework (e.g.,
> [pre-commit](https://pre-commit.com/)) to manage git hooks declaratively
> and install them automatically via `pre-commit install`.

---

## Testing the Hooks

### Test 1: Claude Code hook blocks private file staging

From within a Claude Code session, ask Claude to run:

```bash
git add KNOWN_ISSUES.md
```

**Expected:** Command is blocked. stderr shows:
```
BLOCKED: 'KNOWN_ISSUES.md' is a private file/directory and must not be staged
for commit. See CLAUDE.md privacy rules.
```

### Test 2: Claude Code hook allows normal file staging

```bash
git add README.md
```

**Expected:** Command executes normally.

### Test 3: Hook script directly (outside Claude Code)

```bash
echo '{"tool_input":{"command":"git add KNOWN_ISSUES.md"}}' | python .claude/hooks/guard-private-files.py
echo "exit code: $?"
# Expected: stderr message, exit code 2

echo '{"tool_input":{"command":"git add README.md"}}' | python .claude/hooks/guard-private-files.py
echo "exit code: $?"
# Expected: no output, exit code 0

echo '{"tool_input":{"command":"python script.py"}}' | python .claude/hooks/guard-private-files.py
echo "exit code: $?"
# Expected: no output, exit code 0 (non-git commands pass through)
```

### Test 4: Git pre-commit hook blocks private file commit

```bash
git add -f KNOWN_ISSUES.md
git commit -m "test"
# Expected: "ERROR: Attempted to commit private file matching 'KNOWN_ISSUES.md'."

# Clean up:
git reset HEAD KNOWN_ISSUES.md
```

### Test 5: Git pre-commit hook allows normal commit

```bash
git add .gitignore
git commit -m "test normal commit"
# Expected: Commit succeeds
```

---

## Maintenance

### Adding a new private file

To protect a new file or directory:

1. **Add to `.gitignore`** — prevents wildcard staging
2. **Add to `.claude/hooks/guard-private-files.py`** — add the pattern to the
   `PRIVATE_PATTERNS` list
3. **Add to `.git/hooks/pre-commit`** — add the pattern to the
   `PRIVATE_PATTERNS` array
4. **Commit** `.gitignore` and `.claude/hooks/guard-private-files.py`

### Removing a protected file

Reverse the steps above: remove the pattern from all three locations and commit.

### Debugging hook failures

If the Claude Code hook is not firing:
- Verify `.claude/settings.json` exists and is valid JSON
- Verify `python` is on PATH
- Check that `$CLAUDE_PROJECT_DIR` resolves correctly (run `echo $CLAUDE_PROJECT_DIR` in a Claude Code session)

If the git pre-commit hook is not firing:
- Verify `.git/hooks/pre-commit` exists and is executable (`chmod +x`)
- Verify it has a valid shebang line (`#!/bin/bash`)
- Check that git is not invoked with `--no-verify`
