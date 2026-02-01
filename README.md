# 🔄 Copilot Ralph Mode

> Implementation of the Ralph Wiggum technique for iterative, self-referential AI development loops with GitHub Copilot.

[![GitHub](https://img.shields.io/badge/GitHub-Copilot-blue)](https://github.com/features/copilot)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Cross-Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

---

## 🤔 What is Ralph?

Ralph is a development methodology based on continuous AI agent loops. As Geoffrey Huntley describes it: **"Ralph is a Bash loop"** - a simple `while true` that repeatedly feeds an AI agent a prompt file, allowing it to iteratively improve its work until completion.

The technique is named after Ralph Wiggum from The Simpsons, embodying the philosophy of persistent iteration despite setbacks.

---

## 🎯 How It Works

```
┌─────────────────────────────────────────────────────┐
│                  Ralph Loop                          │
│                                                      │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐   │
│   │  Prompt  │────▶│  Copilot │────▶│   Work   │   │
│   │   File   │     │  Reads   │     │  on Task │   │
│   └──────────┘     └──────────┘     └────┬─────┘   │
│        ▲                                  │         │
│        │           ┌──────────┐           │         │
│        └───────────│  Check   │◀──────────┘         │
│                    │ Complete │                      │
│                    └────┬─────┘                      │
│                         │                            │
│              ┌──────────┴──────────┐                │
│              │                     │                 │
│              ▼                     ▼                 │
│        [Not Done]            [Done! ✅]              │
│         Continue               Exit                  │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/sepehrbayat/copilot-ralph-mode.git
cd copilot-ralph-mode

# Make executable (Linux/macOS)
chmod +x ralph_mode.py ralph-mode.sh

# Or use directly with Python (all platforms)
python ralph_mode.py --help
```

### Enable Ralph Mode

```bash
# Linux/macOS
./ralph_mode.py enable "Build a REST API for todos" --max-iterations 20 --completion-promise "DONE"

# Windows (PowerShell)
python ralph_mode.py enable "Build a REST API for todos" --max-iterations 20 --completion-promise "DONE"

# Windows (CMD)
ralph-mode.cmd enable "Build a REST API for todos" --max-iterations 20 --completion-promise "DONE"
```

### Check Status

```bash
python ralph_mode.py status
```

### Disable Ralph Mode

```bash
python ralph_mode.py disable
```

---

## 📦 Cross-Platform Support

| Platform | Command |
|----------|---------|
| **Linux/macOS** | `./ralph_mode.py` or `./ralph-mode.sh` |
| **Windows PowerShell** | `python ralph_mode.py` or `.\ralph-mode.ps1` |
| **Windows CMD** | `python ralph_mode.py` or `ralph-mode.cmd` |

### Requirements

- Python 3.7 or higher
- No external dependencies (uses only Python standard library)
- Optional: `colorama` for colored output on Windows

---

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `enable <prompt>` | Enable Ralph mode with the given prompt |
| `batch-init --tasks-file <path>` | Initialize batch mode with multiple tasks |
| `disable` | Disable Ralph mode |
| `status` | Show current status |
| `prompt` | Show current prompt |
| `iterate` | Increment iteration counter |
| `next-task` | Move to next task in batch mode |
| `complete <output>` | Check if output contains completion promise |
| `history` | Show iteration history |
| `help` | Show help message |

### Enable Options

| Option | Description |
|--------|-------------|
| `--max-iterations <n>` | Maximum iterations (default: 0 = unlimited) |
| `--completion-promise <text>` | Phrase that signals completion |

### Batch Mode Options

| Option | Description |
|--------|-------------|
| `--tasks-file <path>` | JSON file with tasks list |
| `--max-iterations <n>` | Maximum iterations per task (default: 20) |
| `--completion-promise <text>` | Phrase that signals completion |

---

## 📦 Batch Mode (Multi-Task)

Batch mode lets you run multiple tasks sequentially. Each task has its own file and can run up to a fixed number of iterations.

### 1) Create a tasks JSON file

```json
[
  {
    "id": "HXA-0004",
    "title": "پیاده‌سازی RTL در همه components",
    "prompt": "تمام کامپوننت‌های UI را RTL کن. تست‌ها را اجرا کن."
  },
  {
    "id": "HXA-0010",
    "title": "AI Gateway Service",
    "prompt": "سرویس AI Gateway را طبق docs/specs پیاده‌سازی کن."
  }
]
```

### 2) Start batch mode

```bash
python ralph_mode.py batch-init --tasks-file tasks.json --max-iterations 20 --completion-promise "DONE"
```

### 3) Move to next task (optional)

```bash
python ralph_mode.py next-task
```

---

## 📝 Prompt Writing Best Practices

### ✅ Good Prompts

```markdown
Build a REST API for todos.

Requirements:
- CRUD endpoints working
- Input validation in place
- Tests passing (coverage > 80%)
- README with API docs

When complete, output: <promise>COMPLETE</promise>
```

### ❌ Bad Prompts

```markdown
Build a todo API and make it good.
```

### Tips

1. **Clear Completion Criteria** - Define exactly what "done" means
2. **Incremental Goals** - Break large tasks into phases
3. **Self-Correction** - Include TDD or verification steps
4. **Escape Hatches** - Always use `--max-iterations` as safety

---

## 🔧 File Structure

When Ralph mode is active, it creates:

```
.ralph-mode/
├── state.json        # Current state (iteration, config)
├── prompt.md         # The task prompt
├── INSTRUCTIONS.md   # Instructions for Copilot
├── history.jsonl     # Iteration history log
├── tasks.json        # Task queue (batch mode)
└── tasks/            # Each task in a separate file
```

### state.json Example

```json
{
  "active": true,
  "iteration": 3,
  "max_iterations": 20,
  "completion_promise": "DONE",
  "started_at": "2026-02-01T18:00:00Z",
  "version": "1.0.0"
}
```

---

## 🎭 Philosophy

Ralph embodies several key principles:

| Principle | Description |
|-----------|-------------|
| **Iteration > Perfection** | Don't aim for perfect on first try. Let the loop refine the work. |
| **Failures Are Data** | "Deterministically bad" means failures are predictable and informative. |
| **Operator Skill Matters** | Success depends on writing good prompts, not just having a good model. |
| **Persistence Wins** | Keep trying until success. The loop handles retry logic automatically. |

---

## ✅ When to Use Ralph

**Good for:**
- Well-defined tasks with clear success criteria
- Tasks requiring iteration and refinement (e.g., getting tests to pass)
- Greenfield projects where you can walk away
- Tasks with automatic verification (tests, linters)

**Not good for:**
- Tasks requiring human judgment or design decisions
- One-shot operations
- Tasks with unclear success criteria
- Production debugging

---

## 🧪 Running Tests

```bash
# Python tests (cross-platform)
python -m pytest tests/ -v

# Or directly
python tests/test_ralph_mode.py

# Bash tests (Linux/macOS only)
bash tests/test-ralph-mode.sh
```

---

## 🌟 Real-World Results

From the original Ralph technique:
- Successfully generated 6 repositories overnight in Y Combinator hackathon testing
- One $50k contract completed for $297 in API costs
- Created entire programming language ("cursed") over 3 months

---

## 📚 Learn More

- [Original Ralph Technique by Geoffrey Huntley](https://ghuntley.com/ralph/)
- [Claude Code Ralph Plugin](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum)
- [Ralph Orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 🙏 Credits

- **Geoffrey Huntley** - Original Ralph technique
- **Anthropic** - Claude Code ralph-wiggum plugin inspiration
- **GitHub Copilot** - AI pair programming

---

## 👤 Author

**Sepehr Bayat**
- GitHub: [@sepehrbayat](https://github.com/sepehrbayat)

---

Made with ❤️ for the AI-assisted development community
