---
name: preflight
description: Pre-flight validation checklist before executing pipeline tasks
user-invocable: true
disable-model-invocation: false
---

# Pre-Flight Checklist

Run before executing any pipeline script, API extractor, or statistical analysis.

## Context Scan (30 seconds)
1. Read `domain-facts.md` — check for relevant patterns, traps, API notes
2. Scan MEMORY.md "Current State" — any blockers for this task?
3. If touching pipeline code: check KNOWN_ISSUES.md for the affected module
4. Grep codebase for existing import/usage patterns of any libraries involved

## Verify Assumptions (1 minute)
5. Read the script to run — verify imports, input files, output paths
6. Verify input parquets exist: `ls -la 01_Data/processed/<file>.parquet`
7. If API calls: verify key is set
8. If numerical data: spot-check for inf/NaN in input data

## Present Plan
9. Write numbered plan with steps, files, commands, duration estimate, risks
10. STOP and wait for user approval

## Smoke Test
11. Run with --sample 1 (NOT --sample 50) or verify 1 cached file
12. Confirm output schema before scaling up
