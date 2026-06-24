# KB Schema

Use plain Markdown with light frontmatter.

## Decision Note

```markdown
---
type: decision
status: active
---

# Decision Title

## Decision

What changed.

## Why It Matters

Why the next agent should remember it.

## Evidence

- command or file path
```

## Session Handoff

```markdown
---
type: session
status: active
---

# Current Agent Handoff

## Current State

What works right now.

## Next Action

The smallest next task.

## Boundaries

Files, commands, or data the next agent must avoid.

## Verification

The command that proves the task worked.
```
