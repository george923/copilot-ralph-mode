#!/bin/bash

# Copilot Ralph Mode
# Implementation of the Ralph Wiggum technique for GitHub Copilot
# https://github.com/YOUR_USERNAME/copilot-ralph-mode

set -euo pipefail

VERSION="1.0.0"
RALPH_DIR=".ralph-mode"
STATE_FILE="$RALPH_DIR/state.md"
INSTRUCTIONS_FILE="$RALPH_DIR/INSTRUCTIONS.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored output
info() { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✅${NC} $1"; }
warning() { echo -e "${YELLOW}⚠️${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1" >&2; }

# Show usage
usage() {
  cat << EOF
🔄 Copilot Ralph Mode v${VERSION}

Usage: ralph-mode.sh <command> [options]

Commands:
  enable <prompt>   Enable Ralph mode with the given prompt
  disable           Disable Ralph mode
  status            Show current Ralph mode status
  prompt            Show the current prompt
  iterate           Increment iteration counter
  help              Show this help message

Options for 'enable':
  --max-iterations <n>        Maximum iterations (default: 0 = unlimited)
  --completion-promise <text> Phrase that signals completion

Examples:
  ralph-mode.sh enable "Build a REST API" --max-iterations 20
  ralph-mode.sh enable "Fix all tests" --completion-promise "ALL TESTS PASS"
  ralph-mode.sh status
  ralph-mode.sh disable

EOF
}

# Create instructions file for Copilot
create_instructions() {
  local completion_promise="$1"
  local max_iterations="$2"
  
  cat > "$INSTRUCTIONS_FILE" << 'EOF'
# 🔄 Ralph Mode Active

## What is Ralph Mode?

Ralph Mode is an iterative development loop where you (Copilot) work on a task repeatedly until completion. The same prompt is fed back to you each iteration, but you see your previous work in files and git history.

## Your Workflow

1. **Read the task** from `.ralph-mode/state.md`
2. **Work on the task** - make changes, run tests, fix issues
3. **Check completion** - are all requirements met?
4. **Signal completion** OR **continue iterating**

## Iteration Rules

- Each iteration, you see your previous work in files
- The prompt stays the SAME - you improve incrementally
- Check `iteration` in state.md to see current iteration
- If `max_iterations` > 0 and you've reached it, stop

## Completion

EOF

  if [[ "$completion_promise" != "null" ]]; then
    cat >> "$INSTRUCTIONS_FILE" << EOF
**To signal completion, output this EXACT text:**

\`\`\`
<promise>${completion_promise}</promise>
\`\`\`

⚠️ **CRITICAL RULES:**
- ONLY output the promise when the task is GENUINELY COMPLETE
- Do NOT lie to exit the loop
- The statement must be completely and unequivocally TRUE
- If stuck, document blockers instead of false promises

EOF
  fi

  if [[ "$max_iterations" -gt 0 ]]; then
    cat >> "$INSTRUCTIONS_FILE" << EOF
**Maximum Iterations:** ${max_iterations}
- Loop will automatically stop after ${max_iterations} iterations
- Current iteration is tracked in state.md

EOF
  fi

  cat >> "$INSTRUCTIONS_FILE" << 'EOF'
## How to Check Status

```bash
cat .ralph-mode/state.md
```

## How to Update Progress

After each significant change:
1. Run tests if applicable
2. Update files with your changes
3. If complete, output the completion promise
4. If not complete, continue working

## Philosophy

- **Iteration > Perfection**: Don't aim for perfect on first try
- **Failures Are Data**: Use errors to improve
- **Persistence Wins**: Keep trying until success
EOF
}

# Enable Ralph mode
cmd_enable() {
  local prompt=""
  local max_iterations=0
  local completion_promise="null"
  local prompt_parts=()

  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case $1 in
      --max-iterations)
        if [[ -z "${2:-}" ]] || [[ ! "$2" =~ ^[0-9]+$ ]]; then
          error "--max-iterations requires a positive number"
          exit 1
        fi
        max_iterations="$2"
        shift 2
        ;;
      --completion-promise)
        if [[ -z "${2:-}" ]]; then
          error "--completion-promise requires a text argument"
          exit 1
        fi
        completion_promise="$2"
        shift 2
        ;;
      *)
        prompt_parts+=("$1")
        shift
        ;;
    esac
  done

  prompt="${prompt_parts[*]}"

  if [[ -z "$prompt" ]]; then
    error "No prompt provided"
    echo ""
    echo "Usage: ralph-mode.sh enable \"Your task description\" [options]"
    exit 1
  fi

  # Create directory
  mkdir -p "$RALPH_DIR"

  # Create state file
  cat > "$STATE_FILE" << EOF
---
active: true
iteration: 1
max_iterations: ${max_iterations}
completion_promise: $(if [[ "$completion_promise" != "null" ]]; then echo "\"$completion_promise\""; else echo "null"; fi)
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---

${prompt}
EOF

  # Create instructions
  create_instructions "$completion_promise" "$max_iterations"

  echo ""
  echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║           🔄 RALPH MODE ENABLED                           ║${NC}"
  echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${CYAN}Iteration:${NC}          1"
  echo -e "${CYAN}Max Iterations:${NC}     $(if [[ $max_iterations -gt 0 ]]; then echo $max_iterations; else echo "unlimited"; fi)"
  echo -e "${CYAN}Completion Promise:${NC} $(if [[ "$completion_promise" != "null" ]]; then echo "$completion_promise"; else echo "none"; fi)"
  echo ""
  echo -e "${YELLOW}📝 Task:${NC}"
  echo "$prompt"
  echo ""
  
  if [[ "$completion_promise" != "null" ]]; then
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}COMPLETION PROMISE REQUIREMENTS${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "To complete this loop, Copilot must output:"
    echo -e "  ${GREEN}<promise>${completion_promise}</promise>${NC}"
    echo ""
    echo "⚠️  ONLY when the statement is GENUINELY TRUE"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
  fi
  echo ""
  success "Ralph mode is now active!"
  info "Copilot will read .ralph-mode/INSTRUCTIONS.md for guidance"
}

# Disable Ralph mode
cmd_disable() {
  if [[ ! -f "$STATE_FILE" ]]; then
    warning "No active Ralph mode found"
    exit 0
  fi

  # Get iteration count before removing
  local iteration=$(grep '^iteration:' "$STATE_FILE" | sed 's/iteration: *//')

  rm -rf "$RALPH_DIR"

  echo ""
  success "Ralph mode disabled (was at iteration $iteration)"
}

# Show status
cmd_status() {
  if [[ ! -f "$STATE_FILE" ]]; then
    echo ""
    echo -e "${YELLOW}Ralph Mode: ${RED}INACTIVE${NC}"
    echo ""
    echo "To enable: ralph-mode.sh enable \"Your task\" --max-iterations 20"
    exit 0
  fi

  # Parse state
  local frontmatter=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE")
  local iteration=$(echo "$frontmatter" | grep '^iteration:' | sed 's/iteration: *//')
  local max_iterations=$(echo "$frontmatter" | grep '^max_iterations:' | sed 's/max_iterations: *//')
  local completion_promise=$(echo "$frontmatter" | grep '^completion_promise:' | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')
  local started_at=$(echo "$frontmatter" | grep '^started_at:' | sed 's/started_at: *//' | sed 's/^"\(.*\)"$/\1/')
  
  # Get prompt
  local prompt=$(awk '/^---$/{i++; next} i>=2' "$STATE_FILE")

  echo ""
  echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║           🔄 RALPH MODE STATUS                            ║${NC}"
  echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${CYAN}Status:${NC}             ${GREEN}ACTIVE${NC}"
  echo -e "${CYAN}Iteration:${NC}          ${iteration}"
  echo -e "${CYAN}Max Iterations:${NC}     $(if [[ $max_iterations -gt 0 ]]; then echo $max_iterations; else echo "unlimited"; fi)"
  echo -e "${CYAN}Completion Promise:${NC} $(if [[ "$completion_promise" != "null" && -n "$completion_promise" ]]; then echo "$completion_promise"; else echo "none"; fi)"
  echo -e "${CYAN}Started At:${NC}         ${started_at}"
  echo ""
  echo -e "${YELLOW}📝 Current Task:${NC}"
  echo "$prompt"
  echo ""
}

# Show prompt
cmd_prompt() {
  if [[ ! -f "$STATE_FILE" ]]; then
    error "No active Ralph mode"
    exit 1
  fi

  awk '/^---$/{i++; next} i>=2' "$STATE_FILE"
}

# Increment iteration
cmd_iterate() {
  if [[ ! -f "$STATE_FILE" ]]; then
    error "No active Ralph mode"
    exit 1
  fi

  local frontmatter=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE")
  local iteration=$(echo "$frontmatter" | grep '^iteration:' | sed 's/iteration: *//')
  local max_iterations=$(echo "$frontmatter" | grep '^max_iterations:' | sed 's/max_iterations: *//')

  local next_iteration=$((iteration + 1))

  # Check max iterations
  if [[ $max_iterations -gt 0 ]] && [[ $next_iteration -gt $max_iterations ]]; then
    warning "Max iterations ($max_iterations) reached!"
    cmd_disable
    exit 0
  fi

  # Update iteration
  local temp_file="${STATE_FILE}.tmp.$$"
  sed "s/^iteration: .*/iteration: $next_iteration/" "$STATE_FILE" > "$temp_file"
  mv "$temp_file" "$STATE_FILE"

  echo -e "🔄 Ralph iteration: ${GREEN}$next_iteration${NC}"
}

# Main
main() {
  local command="${1:-help}"

  case "$command" in
    enable)
      shift
      cmd_enable "$@"
      ;;
    disable)
      cmd_disable
      ;;
    status)
      cmd_status
      ;;
    prompt)
      cmd_prompt
      ;;
    iterate)
      cmd_iterate
      ;;
    help|--help|-h)
      usage
      ;;
    version|--version|-v)
      echo "Copilot Ralph Mode v${VERSION}"
      ;;
    *)
      error "Unknown command: $command"
      echo ""
      usage
      exit 1
      ;;
  esac
}

main "$@"
