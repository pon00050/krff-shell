---
name: push
description: End-of-session push workflow with doc updates and test verification
user-invocable: true
disable-model-invocation: true
---

# Push Workflow

Before pushing, complete these steps in order:

1. Update `session-history.md` (in auto-memory at `~/.claude/projects/.../memory/session-history.md`) with a summary of this session's work
2. Update `CHANGELOG.md` if any user-facing changes were made
3. Update `ROADMAP.md` to reflect any completed items
4. Run `python -m pytest tests/test_pipeline_invariants.py -v` and confirm all tests pass
5. Run `git status` and verify no private files are staged (check against Privacy Rule in CLAUDE.md)
6. Stage specific files by name (never `git add -A` or `git add .`)
7. Commit with a descriptive message
8. Push and confirm CI goes green
