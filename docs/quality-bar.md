# Quality Bar

Good vibe coding still has a quality bar.

## What Good Looks Like

- The task is small enough to review.
- The agent has project context before it edits.
- Tests and checks are run after the edit.
- Security-sensitive changes get an extra review.
- Durable decisions are written down once, then reused.

## Prompt Shape

Use this shape when asking a coding agent for work:

```text
Context: what repo or feature this touches.
Goal: the smallest useful change.
Constraints: files to avoid, APIs to preserve, security rules.
Verification: exact command the agent must run before it stops.
Memory: what decision should be saved if the result matters later.
```

## Quality Gate

Run this before trusting a patch:

```bash
python3 scripts/quality_gate.py
```

The gate checks:

- Python files compile
- unit tests pass
- unsafe code patterns are not present in the app or helper scripts
- agent instructions and tool configs still point at the same workflow

## Security Line

Do not let a coding agent read, print, commit, or summarize secrets. Fake samples are fine. Real tokens, cookies, cloud credentials, and private customer data are not lab material.

