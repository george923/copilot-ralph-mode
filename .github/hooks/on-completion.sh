#!/usr/bin/env bash
# Completion hook for Ralph Mode
# This hook runs when a task is completed (completion promise detected)
#
# Environment variables available:
#   RALPH_ITERATION - Final iteration number
#   RALPH_TASK_ID - Completed task ID
#   RALPH_MODE - "single" or "batch"
#   RALPH_PROMISE - The completion promise that was detected

# Example: Log completion
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Task completed at iteration $RALPH_ITERATION" >> .ralph-mode/hooks.log

# Example: Send notification
# curl -X POST "https://hooks.slack.com/..." -d '{"text":"Ralph completed task"}' 2>/dev/null || true

# Example: Create a summary
# echo "## Task Completed" > .ralph-mode/summary.md
# echo "- Iterations: $RALPH_ITERATION" >> .ralph-mode/summary.md
# echo "- Task: $RALPH_TASK_ID" >> .ralph-mode/summary.md

exit 0
