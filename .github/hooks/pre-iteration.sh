#!/usr/bin/env bash
# Pre-iteration hook for Ralph Mode
# This hook runs BEFORE each Copilot CLI iteration
#
# Environment variables available:
#   RALPH_ITERATION - Current iteration number
#   RALPH_MAX_ITERATIONS - Maximum iterations allowed
#   RALPH_TASK_ID - Current task ID (in batch mode)
#   RALPH_MODE - "single" or "batch"

# Example: Log iteration start
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting iteration $RALPH_ITERATION" >> .ralph-mode/hooks.log

# Example: Run linting before each iteration
# npm run lint --silent 2>/dev/null || true

# Example: Check disk space
# df -h . | tail -1

# Return 0 to continue, non-zero to abort
exit 0
