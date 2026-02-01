# 🔄 Copilot Ralph Mode

> Implementation of the Ralph Wiggum technique for iterative, self-referential AI development loops with GitHub Copilot.

[![GitHub](https://img.shields.io/badge/GitHub-Copilot-blue)](https://github.com/features/copilot)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

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

### 1. Enable Ralph Mode

```bash
# In your project directory
./ralph-mode.sh enable "Your task description" --max-iterations 20 --completion-promise "DONE"
```

### 2. Work with Copilot

Just work normally! When you ask Copilot to do something, it will:
1. Read the active Ralph prompt
2. Work on the task
3. Check if completion criteria met
4. If not done → continue iterating

### 3. Disable Ralph Mode

```bash
./ralph-mode.sh disable
```

---

## 📦 Installation

```bash
# Clone this repo
git clone https://github.com/YOUR_USERNAME/copilot-ralph-mode.git

# Copy to your project
cp -r copilot-ralph-mode/.ralph-mode your-project/

# Or install globally
ln -s $(pwd)/copilot-ralph-mode/ralph-mode.sh /usr/local/bin/ralph-mode
```

---

## 🛠️ Commands

### Enable Ralph Mode
```bash
./ralph-mode.sh enable "<prompt>" [OPTIONS]

Options:
  --max-iterations <n>        Maximum iterations (default: unlimited)
  --completion-promise <text> Phrase that signals completion
```

### Disable Ralph Mode
```bash
./ralph-mode.sh disable
```

### Check Status
```bash
./ralph-mode.sh status
```

### View Current Prompt
```bash
./ralph-mode.sh prompt
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

---

## 🔧 Configuration Files

### `.ralph-mode/state.md`

```yaml
---
active: true
iteration: 1
max_iterations: 20
completion_promise: "DONE"
started_at: "2026-02-01T17:00:00Z"
---

Your task prompt goes here...
```

### `.ralph-mode/INSTRUCTIONS.md`

Instructions for Copilot on how to work in Ralph mode.

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

Contributions are welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

Made with ❤️ for the AI-assisted development community
