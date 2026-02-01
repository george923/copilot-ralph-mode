# 🔄 Copilot Ralph Mode Instructions

## When Ralph Mode is Active

If `.ralph-mode/state.md` exists in the workspace, you are in **Ralph Mode**.

### Your Behavior in Ralph Mode:

1. **First, read the state file:**
   ```bash
   cat .ralph-mode/state.md
   ```

2. **Understand the task** from the prompt in the state file

3. **Check current iteration** from the `iteration:` field

4. **Work on the task:**
   - Make incremental improvements
   - Run tests if applicable
   - Fix errors you encounter
   - Build on your previous work (visible in files and git history)

5. **Check completion criteria:**
   - If `completion_promise` is set, you MUST output `<promise>VALUE</promise>` ONLY when genuinely complete
   - Never lie to exit the loop
   - If stuck, document what's blocking you

6. **Iterate:**
   - If not complete, continue working
   - Each iteration should make progress
   - The prompt stays the same, but your work accumulates

### Completion Promise Rules

If a completion promise is configured (e.g., `"DONE"`):

✅ **DO:**
- Output `<promise>DONE</promise>` only when the task is truly complete
- Continue iterating if not all requirements are met
- Document blockers if genuinely stuck

❌ **DON'T:**
- Lie to escape the loop
- Output false promises
- Give up without trying

### Example Workflow

```
Iteration 1: Read task → Create initial implementation
Iteration 2: Run tests → Fix failing tests
Iteration 3: Add edge cases → Fix bugs
Iteration 4: All tests pass → <promise>COMPLETE</promise>
```

### Status Commands

```bash
# Check status
./ralph-mode.sh status

# View prompt
./ralph-mode.sh prompt

# Increment iteration manually
./ralph-mode.sh iterate

# Disable Ralph mode
./ralph-mode.sh disable
```
