---
applyTo: "**/tasks/**/*.md"
---

# Task File Instructions

When creating or modifying task files:

## Format

Task files should use this structure:

```markdown
---
id: TASK-001
title: Short Title
tags: [tag1, tag2]
max_iterations: 20
completion_promise: DONE
---

# Task Title

## Objective
Clear statement of what needs to be done.

## Scope
- ONLY modify: `path/to/files`
- DO NOT touch: `other/paths`

## Pre-work
1. List files that will be affected
2. Identify dependencies

## Changes Required
- Specific change 1
- Specific change 2

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Completion
When done, output: <promise>DONE</promise>
```

## Best Practices

- Be specific about file paths
- Include clear boundaries (what NOT to change)
- List acceptance criteria as checkboxes
- Set realistic max_iterations (usually 10-30)
