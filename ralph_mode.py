#!/usr/bin/env python3
"""
Copilot Ralph Mode - Cross-platform implementation
Implementation of the Ralph Wiggum technique for GitHub Copilot

Usage:
    ralph-mode enable "Your task" --max-iterations 20 --completion-promise "DONE"
    ralph-mode batch-init --tasks-file tasks.json --max-iterations 20 --completion-promise "DONE"
    ralph-mode disable
    ralph-mode status
    ralph-mode iterate
    ralph-mode next-task
    ralph-mode prompt
    ralph-mode help
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

VERSION = "1.0.0"

# ANSI Colors (disabled on Windows without colorama)
class Colors:
    """ANSI color codes for terminal output."""
    
    def __init__(self):
        self.enabled = self._check_color_support()
        
    def _check_color_support(self) -> bool:
        """Check if terminal supports colors."""
        if os.name == 'nt':  # Windows
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                return os.environ.get('TERM') is not None
        return sys.stdout.isatty()
    
    @property
    def RED(self) -> str:
        return '\033[0;31m' if self.enabled else ''
    
    @property
    def GREEN(self) -> str:
        return '\033[0;32m' if self.enabled else ''
    
    @property
    def YELLOW(self) -> str:
        return '\033[1;33m' if self.enabled else ''
    
    @property
    def BLUE(self) -> str:
        return '\033[0;34m' if self.enabled else ''
    
    @property
    def CYAN(self) -> str:
        return '\033[0;36m' if self.enabled else ''
    
    @property
    def NC(self) -> str:
        return '\033[0m' if self.enabled else ''


colors = Colors()


class RalphMode:
    """Main Ralph Mode controller."""
    
    RALPH_DIR = ".ralph-mode"
    STATE_FILE = "state.json"
    PROMPT_FILE = "prompt.md"
    INSTRUCTIONS_FILE = "INSTRUCTIONS.md"
    HISTORY_FILE = "history.jsonl"
    TASKS_DIR = "tasks"
    TASKS_INDEX = "tasks.json"
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize Ralph Mode with optional base path."""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.ralph_dir = self.base_path / self.RALPH_DIR
        self.state_file = self.ralph_dir / self.STATE_FILE
        self.prompt_file = self.ralph_dir / self.PROMPT_FILE
        self.instructions_file = self.ralph_dir / self.INSTRUCTIONS_FILE
        self.history_file = self.ralph_dir / self.HISTORY_FILE
        self.tasks_dir = self.ralph_dir / self.TASKS_DIR
        self.tasks_index = self.ralph_dir / self.TASKS_INDEX
    
    def is_active(self) -> bool:
        """Check if Ralph mode is currently active."""
        return self.state_file.exists()
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current Ralph mode state."""
        if not self.is_active():
            return None
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save Ralph mode state."""
        self.ralph_dir.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def get_prompt(self) -> Optional[str]:
        """Get current prompt."""
        if not self.prompt_file.exists():
            return None
        return self.prompt_file.read_text(encoding='utf-8')
    
    def save_prompt(self, prompt: str) -> None:
        """Save prompt to file."""
        self.ralph_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_file.write_text(prompt, encoding='utf-8')

    def load_tasks(self) -> list:
        """Load tasks list from tasks.json."""
        if not self.tasks_index.exists():
            return []
        try:
            with open(self.tasks_index, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_tasks(self, tasks: list) -> None:
        """Save tasks list to tasks.json."""
        self.ralph_dir.mkdir(parents=True, exist_ok=True)
        with open(self.tasks_index, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _slugify(text: str) -> str:
        """Create a filesystem-safe slug from text."""
        text = re.sub(r'[^a-zA-Z0-9\-_.]+', '-', text.strip())
        text = re.sub(r'-{2,}', '-', text).strip('-')
        return text.lower() or "task"

    def _task_filename(self, index: int, task_id: str, title: str) -> str:
        """Generate a filename for a task."""
        base = task_id or title
        slug = self._slugify(base)
        return f"{index + 1:02d}-{slug}.md"

    def _write_task_files(self, tasks: list) -> list:
        """Write tasks to individual files and return normalized task list."""
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        normalized = []

        for idx, task in enumerate(tasks):
            if isinstance(task, str):
                task_id = f"TASK-{idx + 1:03d}"
                title = task
                prompt = task
            else:
                task_id = task.get('id') or f"TASK-{idx + 1:03d}"
                title = task.get('title') or task.get('prompt') or task_id
                prompt = task.get('prompt') or title

            filename = self._task_filename(idx, task_id, title)
            task_path = self.tasks_dir / filename

            content = f"# {task_id} — {title}\n\n{prompt}\n"
            task_path.write_text(content, encoding='utf-8')

            normalized.append({
                "id": task_id,
                "title": title,
                "prompt": prompt,
                "file": str(task_path)
            })

        return normalized

    def _set_current_task(self, state: Dict[str, Any], tasks: list) -> None:
        """Set current task info in state and update prompt.md."""
        index = state.get('current_task_index', 0)
        if index < 0 or index >= len(tasks):
            raise ValueError("Current task index is out of range.")

        current = tasks[index]
        state['current_task_id'] = current.get('id')
        state['current_task_title'] = current.get('title')
        state['current_task_file'] = current.get('file')
        self.save_prompt(current.get('prompt') or current.get('title') or "")
    
    def log_iteration(self, iteration: int, status: str, notes: str = "") -> None:
        """Log iteration to history file."""
        entry = {
            "iteration": iteration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "notes": notes
        }
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def create_instructions(self, completion_promise: Optional[str], max_iterations: int, mode: str = "single") -> None:
        """Create instructions file for Copilot."""
        content = """# 🔄 Ralph Mode Active

## What is Ralph Mode?

Ralph Mode is an iterative development loop where you (Copilot) work on a task repeatedly until completion. The same prompt is fed back to you each iteration, but you see your previous work in files and git history.

## Your Workflow

1. **Read the task** from `.ralph-mode/prompt.md`
2. **Check state** from `.ralph-mode/state.json` (current iteration, limits)
3. **Work on the task** - make changes, run tests, fix issues
4. **Check completion** - are all requirements met?
5. **Signal completion** OR **continue iterating**

## Iteration Rules

- Each iteration, you see your previous work in files
- The prompt stays the SAME - you improve incrementally
- Check `iteration` in state.json to see current iteration
- If `max_iterations` > 0 and you've reached it, stop

## Current State

Read `.ralph-mode/state.json` for:
- `iteration`: Current iteration number
- `max_iterations`: Maximum allowed (0 = unlimited)
- `completion_promise`: Text to output when done
- `started_at`: When the loop started

"""

        if mode == "batch":
            content += """## Task Queue (Batch Mode)

- Tasks are stored in `.ralph-mode/tasks/`
- Task list is stored in `.ralph-mode/tasks.json`
- Current task is tracked in `state.json` (`current_task_index`, `current_task_id`)

"""
        
        if completion_promise:
            content += f"""## Completion

**To signal completion, output this EXACT text:**

```
<promise>{completion_promise}</promise>
```

⚠️ **CRITICAL RULES:**
- ONLY output the promise when the task is GENUINELY COMPLETE
- Do NOT lie to exit the loop
- The statement must be completely and unequivocally TRUE
- If stuck, document blockers instead of false promises

"""
        
        if max_iterations > 0:
            content += f"""## Iteration Limit

**Maximum Iterations:** {max_iterations}
- Loop will automatically stop after {max_iterations} iterations
- Current iteration is tracked in state.json

"""
        
        content += """## How to Check Status

```bash
# Cross-platform
python ralph-mode.py status

# Or read directly
cat .ralph-mode/state.json
cat .ralph-mode/prompt.md
```

## Philosophy

- **Iteration > Perfection**: Don't aim for perfect on first try
- **Failures Are Data**: Use errors to improve
- **Persistence Wins**: Keep trying until success

## History

All iterations are logged in `.ralph-mode/history.jsonl` for review.
"""
        
        self.instructions_file.write_text(content, encoding='utf-8')
    
    def enable(self, prompt: str, max_iterations: int = 0, 
               completion_promise: Optional[str] = None) -> Dict[str, Any]:
        """Enable Ralph mode with the given configuration."""
        
        if self.is_active():
            current = self.get_state()
            raise ValueError(f"Ralph mode is already active (iteration {current.get('iteration', '?')}). "
                           "Use 'disable' first or 'iterate' to continue.")
        
        state = {
            "active": True,
            "iteration": 1,
            "max_iterations": max_iterations,
            "completion_promise": completion_promise,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "version": VERSION,
            "mode": "single"
        }
        
        self.ralph_dir.mkdir(parents=True, exist_ok=True)
        self.save_state(state)
        self.save_prompt(prompt)
        self.create_instructions(completion_promise, max_iterations, mode="single")
        self.log_iteration(1, "started", f"Prompt: {prompt[:100]}...")
        
        return state

    def init_batch(self, tasks: list, max_iterations: int = 20,
                   completion_promise: Optional[str] = None) -> Dict[str, Any]:
        """Initialize batch mode with multiple tasks."""
        if self.is_active():
            current = self.get_state()
            raise ValueError(
                f"Ralph mode is already active (iteration {current.get('iteration', '?')}). "
                "Use 'disable' first or 'iterate' to continue."
            )

        if not tasks:
            raise ValueError("Task list is empty. Provide at least one task.")

        normalized = self._write_task_files(tasks)
        self.save_tasks(normalized)

        state = {
            "active": True,
            "iteration": 1,
            "max_iterations": max_iterations,
            "completion_promise": completion_promise,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "version": VERSION,
            "mode": "batch",
            "current_task_index": 0,
            "tasks_total": len(normalized)
        }

        self._set_current_task(state, normalized)
        self.save_state(state)
        self.create_instructions(completion_promise, max_iterations, mode="batch")
        self.log_iteration(1, "batch_started", f"Tasks: {len(normalized)}")

        return state

    def next_task(self, reason: str = "completed") -> Dict[str, Any]:
        """Advance to the next task in batch mode."""
        state = self.get_state()
        if not state:
            raise ValueError("State file corrupted. Please disable and re-enable.")

        if state.get("mode") != "batch":
            raise ValueError("next_task is only available in batch mode.")

        tasks = self.load_tasks()
        if not tasks:
            raise ValueError("Tasks list is missing or corrupted.")

        current_index = state.get("current_task_index", 0)
        self.log_iteration(state.get('iteration', 0), f"task_{reason}",
                           f"Task {current_index + 1}/{len(tasks)}")

        next_index = current_index + 1
        if next_index >= len(tasks):
            self.disable()
            raise ValueError("All tasks completed. Ralph mode disabled.")

        state['current_task_index'] = next_index
        state['iteration'] = 1
        state['last_iterate_at'] = datetime.now(timezone.utc).isoformat()
        self._set_current_task(state, tasks)
        self.save_state(state)

        return state
    
    def disable(self) -> Optional[Dict[str, Any]]:
        """Disable Ralph mode and return final state."""
        if not self.is_active():
            return None
        
        state = self.get_state()
        if state:
            self.log_iteration(state.get('iteration', 0), "disabled", "Ralph mode disabled by user")
        
        # Remove all files
        import shutil
        if self.ralph_dir.exists():
            shutil.rmtree(self.ralph_dir)
        
        return state
    
    def iterate(self) -> Dict[str, Any]:
        """Increment iteration counter and return new state."""
        if not self.is_active():
            raise ValueError("No active Ralph mode. Use 'enable' first.")
        
        state = self.get_state()
        if not state:
            raise ValueError("State file corrupted. Please disable and re-enable.")
        
        max_iter = state.get('max_iterations', 0)
        current_iter = state.get('iteration', 1)
        
        # Check if max iterations reached
        if max_iter > 0 and current_iter >= max_iter:
            if state.get("mode") == "batch":
                self.log_iteration(current_iter, "max_reached",
                                 f"Max iterations ({max_iter}) reached for task")
                return self.next_task(reason="max_reached")

            self.log_iteration(current_iter, "max_reached", 
                             f"Max iterations ({max_iter}) reached")
            self.disable()
            raise ValueError(f"Max iterations ({max_iter}) reached. Ralph mode disabled.")
        
        # Increment
        state['iteration'] = current_iter + 1
        state['last_iterate_at'] = datetime.now(timezone.utc).isoformat()
        self.save_state(state)
        self.log_iteration(state['iteration'], "iterate", "Iteration incremented")
        
        return state
    
    def check_completion(self, output_text: str) -> bool:
        """Check if output contains completion promise."""
        state = self.get_state()
        if not state:
            return False
        
        promise = state.get('completion_promise')
        if not promise:
            return False
        
        # Look for <promise>TEXT</promise>
        pattern = r'<promise>(.*?)</promise>'
        matches = re.findall(pattern, output_text, re.DOTALL)
        
        for match in matches:
            if match.strip() == promise:
                self.log_iteration(state.get('iteration', 0), "completed", 
                                 f"Completion promise detected: {promise}")
                return True
        
        return False
    
    def complete(self, output_text: str) -> bool:
        """Check completion and disable if complete."""
        if self.check_completion(output_text):
            state = self.get_state() or {}
            if state.get("mode") == "batch":
                self.next_task(reason="completed")
                return True

            self.disable()
            return True
        return False
    
    def status(self) -> Optional[Dict[str, Any]]:
        """Get full status including prompt."""
        if not self.is_active():
            return None
        
        state = self.get_state()
        if state:
            state['prompt'] = self.get_prompt()
            state['history_entries'] = self._count_history_entries()
            if state.get("mode") == "batch":
                state['tasks_total'] = state.get('tasks_total', 0)
                state['current_task_index'] = state.get('current_task_index', 0)
                state['current_task_number'] = state.get('current_task_index', 0) + 1
                state['current_task_id'] = state.get('current_task_id')
                state['current_task_title'] = state.get('current_task_title')
                state['current_task_file'] = state.get('current_task_file')
        
        return state
    
    def _count_history_entries(self) -> int:
        """Count entries in history file."""
        if not self.history_file.exists():
            return 0
        return sum(1 for _ in open(self.history_file, encoding='utf-8'))
    
    def get_history(self) -> list:
        """Get all history entries."""
        if not self.history_file.exists():
            return []
        
        entries = []
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return entries


def print_banner(title: str) -> None:
    """Print a colored banner."""
    width = 60
    print()
    print(f"{colors.GREEN}╔{'═' * width}╗{colors.NC}")
    print(f"{colors.GREEN}║{title:^{width}}║{colors.NC}")
    print(f"{colors.GREEN}╚{'═' * width}╝{colors.NC}")
    print()


def cmd_enable(args) -> int:
    """Handle enable command."""
    ralph = RalphMode()
    
    prompt = ' '.join(args.prompt) if args.prompt else ''
    if not prompt:
        print(f"{colors.RED}❌ Error: No prompt provided{colors.NC}")
        print("\nUsage: ralph-mode enable \"Your task description\" [options]")
        return 1
    
    try:
        state = ralph.enable(
            prompt=prompt,
            max_iterations=args.max_iterations,
            completion_promise=args.completion_promise
        )
    except ValueError as e:
        print(f"{colors.RED}❌ Error: {e}{colors.NC}")
        return 1
    
    print_banner("🔄 RALPH MODE ENABLED")
    
    print(f"{colors.CYAN}Iteration:{colors.NC}          1")
    print(f"{colors.CYAN}Max Iterations:{colors.NC}     {args.max_iterations if args.max_iterations > 0 else 'unlimited'}")
    print(f"{colors.CYAN}Completion Promise:{colors.NC} {args.completion_promise or 'none'}")
    print()
    print(f"{colors.YELLOW}📝 Task:{colors.NC}")
    print(prompt)
    print()
    
    if args.completion_promise:
        print(f"{colors.YELLOW}{'═' * 60}{colors.NC}")
        print(f"{colors.YELLOW}COMPLETION PROMISE REQUIREMENTS{colors.NC}")
        print(f"{colors.YELLOW}{'═' * 60}{colors.NC}")
        print()
        print("To complete this loop, Copilot must output:")
        print(f"  {colors.GREEN}<promise>{args.completion_promise}</promise>{colors.NC}")
        print()
        print("⚠️  ONLY when the statement is GENUINELY TRUE")
        print(f"{colors.YELLOW}{'═' * 60}{colors.NC}")
    
    print()
    print(f"{colors.GREEN}✅ Ralph mode is now active!{colors.NC}")
    print(f"{colors.BLUE}ℹ Copilot will read .ralph-mode/INSTRUCTIONS.md for guidance{colors.NC}")
    
    return 0


def _load_tasks_from_file(tasks_file: str) -> list:
    """Load tasks from a JSON file."""
    path = Path(tasks_file)
    if not path.exists():
        raise ValueError(f"Tasks file not found: {tasks_file}")

    if path.suffix.lower() != ".json":
        raise ValueError("Tasks file must be a .json file")

    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in tasks file: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Tasks file must contain a JSON array")

    return data


def cmd_batch_init(args) -> int:
    """Handle batch-init command."""
    ralph = RalphMode()

    try:
        tasks = _load_tasks_from_file(args.tasks_file)
        state = ralph.init_batch(
            tasks=tasks,
            max_iterations=args.max_iterations,
            completion_promise=args.completion_promise
        )
    except ValueError as e:
        print(f"{colors.RED}❌ Error: {e}{colors.NC}")
        return 1

    print_banner("🔄 RALPH MODE BATCH STARTED")
    print(f"{colors.CYAN}Mode:{colors.NC}             batch")
    print(f"{colors.CYAN}Tasks Total:{colors.NC}      {state.get('tasks_total')}")
    print(f"{colors.CYAN}Current Task:{colors.NC}     1/{state.get('tasks_total')}")
    print(f"{colors.CYAN}Iteration:{colors.NC}        1")
    print(f"{colors.CYAN}Max Iterations:{colors.NC}   {args.max_iterations}")
    print(f"{colors.CYAN}Completion Promise:{colors.NC} {args.completion_promise or 'none'}")
    print()
    print(f"{colors.YELLOW}📝 Current Task:{colors.NC}")
    print(state.get('current_task_title') or "")
    print()
    print(f"{colors.GREEN}✅ Ralph batch mode is now active!{colors.NC}")
    print(f"{colors.BLUE}ℹ Copilot will read .ralph-mode/INSTRUCTIONS.md for guidance{colors.NC}")

    return 0


def cmd_next_task(args) -> int:
    """Handle next-task command."""
    ralph = RalphMode()

    try:
        state = ralph.next_task(reason="manual_next")
    except ValueError as e:
        print(f"{colors.YELLOW}⚠️ {e}{colors.NC}")
        return 1

    print(f"🔄 Moved to next task: {state.get('current_task_index', 0) + 1}/{state.get('tasks_total', 0)}")
    print(f"{colors.YELLOW}📝 Current Task:{colors.NC} {state.get('current_task_title') or ''}")
    return 0


def cmd_disable(args) -> int:
    """Handle disable command."""
    ralph = RalphMode()
    
    state = ralph.disable()
    if state:
        print()
        print(f"{colors.GREEN}✅ Ralph mode disabled (was at iteration {state.get('iteration', '?')}){colors.NC}")
    else:
        print(f"{colors.YELLOW}⚠️ No active Ralph mode found{colors.NC}")
    
    return 0


def cmd_status(args) -> int:
    """Handle status command."""
    ralph = RalphMode()
    
    status = ralph.status()
    if not status:
        print()
        print(f"{colors.YELLOW}Ralph Mode: {colors.RED}INACTIVE{colors.NC}")
        print()
        print("To enable: ralph-mode enable \"Your task\" --max-iterations 20")
        return 0
    
    print_banner("🔄 RALPH MODE STATUS")
    
    print(f"{colors.CYAN}Status:{colors.NC}             {colors.GREEN}ACTIVE{colors.NC}")
    print(f"{colors.CYAN}Mode:{colors.NC}               {status.get('mode', 'single')}")
    print(f"{colors.CYAN}Iteration:{colors.NC}          {status.get('iteration', '?')}")
    max_iter = status.get('max_iterations', 0)
    print(f"{colors.CYAN}Max Iterations:{colors.NC}     {max_iter if max_iter > 0 else 'unlimited'}")
    promise = status.get('completion_promise')
    print(f"{colors.CYAN}Completion Promise:{colors.NC} {promise if promise else 'none'}")
    print(f"{colors.CYAN}Started At:{colors.NC}         {status.get('started_at', '?')}")
    print(f"{colors.CYAN}History Entries:{colors.NC}    {status.get('history_entries', 0)}")
    if status.get('mode') == 'batch':
        print(f"{colors.CYAN}Tasks Total:{colors.NC}        {status.get('tasks_total', 0)}")
        print(f"{colors.CYAN}Current Task:{colors.NC}       {status.get('current_task_number', 0)}/{status.get('tasks_total', 0)}")
        print(f"{colors.CYAN}Current Task ID:{colors.NC}    {status.get('current_task_id') or 'n/a'}")
    print()
    print(f"{colors.YELLOW}📝 Current Task:{colors.NC}")
    print(status.get('prompt', 'No prompt found'))
    print()
    
    return 0


def cmd_prompt(args) -> int:
    """Handle prompt command."""
    ralph = RalphMode()
    
    if not ralph.is_active():
        print(f"{colors.RED}❌ No active Ralph mode{colors.NC}")
        return 1
    
    prompt = ralph.get_prompt()
    if prompt:
        print(prompt)
    else:
        print(f"{colors.RED}❌ No prompt found{colors.NC}")
        return 1
    
    return 0


def cmd_iterate(args) -> int:
    """Handle iterate command."""
    ralph = RalphMode()
    
    try:
        state = ralph.iterate()
        print(f"🔄 Ralph iteration: {colors.GREEN}{state['iteration']}{colors.NC}")
    except ValueError as e:
        print(f"{colors.YELLOW}⚠️ {e}{colors.NC}")
        return 1
    
    return 0


def cmd_complete(args) -> int:
    """Handle complete command - check if output contains promise."""
    ralph = RalphMode()
    
    if not ralph.is_active():
        print(f"{colors.RED}❌ No active Ralph mode{colors.NC}")
        return 1
    
    # Read output from stdin or argument
    if args.output:
        output = ' '.join(args.output)
    else:
        output = sys.stdin.read()
    
    if ralph.complete(output):
        state = ralph.get_state()
        if state and state.get('mode') == 'batch':
            print(f"{colors.GREEN}✅ Completion promise detected! Moved to next task.{colors.NC}")
            return 0

        print(f"{colors.GREEN}✅ Completion promise detected! Ralph mode disabled.{colors.NC}")
        return 0
    else:
        print(f"{colors.YELLOW}⚠️ No completion promise found. Continue iterating.{colors.NC}")
        return 1


def cmd_history(args) -> int:
    """Handle history command."""
    ralph = RalphMode()
    
    history = ralph.get_history()
    if not history:
        print("No history found.")
        return 0
    
    print(f"\n{'Iteration':<12} {'Status':<15} {'Timestamp':<25} Notes")
    print("-" * 80)
    
    for entry in history:
        print(f"{entry.get('iteration', '?'):<12} "
              f"{entry.get('status', '?'):<15} "
              f"{entry.get('timestamp', '?')[:19]:<25} "
              f"{entry.get('notes', '')[:30]}")
    
    print()
    return 0


def cmd_help(args) -> int:
    """Handle help command."""
    print(f"""
{colors.GREEN}🔄 Copilot Ralph Mode v{VERSION}{colors.NC}

Implementation of the Ralph Wiggum technique for iterative,
self-referential AI development loops with GitHub Copilot.

{colors.YELLOW}USAGE:{colors.NC}
    ralph-mode <command> [options]

{colors.YELLOW}COMMANDS:{colors.NC}
    enable      Enable Ralph mode with a prompt
    batch-init  Initialize batch mode with multiple tasks
    disable     Disable Ralph mode
    status      Show current status
    prompt      Show current prompt
    iterate     Increment iteration counter
    next-task   Move to next task in batch mode
    complete    Check if output contains completion promise
    history     Show iteration history
    help        Show this help message

{colors.YELLOW}ENABLE OPTIONS:{colors.NC}
    --max-iterations <n>        Maximum iterations (default: 0 = unlimited)
    --completion-promise <text> Phrase that signals completion

{colors.YELLOW}BATCH OPTIONS:{colors.NC}
    --tasks-file <path>          JSON file with tasks list
    --max-iterations <n>         Maximum iterations per task (default: 20)
    --completion-promise <text>  Phrase that signals completion

{colors.YELLOW}EXAMPLES:{colors.NC}
    ralph-mode enable "Build a REST API" --max-iterations 20
    ralph-mode batch-init --tasks-file tasks.json --max-iterations 20
    ralph-mode enable "Fix tests" --completion-promise "ALL PASS"
    ralph-mode status
    ralph-mode iterate
    ralph-mode next-task
    ralph-mode disable

{colors.YELLOW}PHILOSOPHY:{colors.NC}
    • Iteration > Perfection
    • Failures Are Data
    • Persistence Wins

{colors.YELLOW}LEARN MORE:{colors.NC}
    • Original technique: https://ghuntley.com/ralph/
    • Claude Code plugin: https://github.com/anthropics/claude-code
""")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='ralph-mode',
        description='Copilot Ralph Mode - Iterative AI development loops'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable Ralph mode')
    enable_parser.add_argument('prompt', nargs='*', help='Task prompt')
    enable_parser.add_argument('--max-iterations', type=int, default=0,
                              help='Maximum iterations (0 = unlimited)')
    enable_parser.add_argument('--completion-promise', type=str, default=None,
                              help='Phrase that signals completion')
    enable_parser.set_defaults(func=cmd_enable)

    # Batch init command
    batch_parser = subparsers.add_parser('batch-init', help='Initialize batch mode')
    batch_parser.add_argument('--tasks-file', required=True, help='Path to tasks JSON file')
    batch_parser.add_argument('--max-iterations', type=int, default=20,
                              help='Maximum iterations per task (default: 20)')
    batch_parser.add_argument('--completion-promise', type=str, default=None,
                              help='Phrase that signals completion')
    batch_parser.set_defaults(func=cmd_batch_init)
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable Ralph mode')
    disable_parser.set_defaults(func=cmd_disable)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show status')
    status_parser.set_defaults(func=cmd_status)
    
    # Prompt command
    prompt_parser = subparsers.add_parser('prompt', help='Show current prompt')
    prompt_parser.set_defaults(func=cmd_prompt)
    
    # Iterate command
    iterate_parser = subparsers.add_parser('iterate', help='Increment iteration')
    iterate_parser.set_defaults(func=cmd_iterate)

    # Next task command
    next_parser = subparsers.add_parser('next-task', help='Move to next task in batch mode')
    next_parser.set_defaults(func=cmd_next_task)
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Check completion')
    complete_parser.add_argument('output', nargs='*', help='Output to check')
    complete_parser.set_defaults(func=cmd_complete)
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show history')
    history_parser.set_defaults(func=cmd_history)
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Show help')
    help_parser.set_defaults(func=cmd_help)
    
    args = parser.parse_args()
    
    if not args.command:
        return cmd_help(args)
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
