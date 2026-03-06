---
name: push
description: End-of-session push workflow with doc updates and test verification
user-invocable: true
disable-model-invocation: true
---

# Push Workflow

## Part 1 — Local bookkeeping (always do)

1. Update `session-history.md` (auto-memory) with a summary of this session's work
2. Update `CHANGELOG.md` (local-only, gitignored) if any user-facing changes were made
3. Update `ROADMAP.md` if any roadmap items were completed

## Part 2 — Repo operations (only if there are uncommitted changes)

Run `git status` first. If working tree is clean and branch is up to date, report
"nothing to push" and stop here.

If there are changes:

4. Run `python -m pytest tests/test_pipeline_invariants.py -v` and confirm all tests pass
5. Verify no private files are staged (check against Privacy Rule in CLAUDE.md)
6. Stage specific files by name (never `git add -A` or `git add .`)
7. Commit with a descriptive message
8. Push and confirm CI goes green
