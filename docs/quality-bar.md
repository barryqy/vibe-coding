# Quality Bar

Good vibe coding still has a quality bar.

## What Good Looks Like

- The task is small enough to review.
- The agent has project context before it edits.
- Tests and checks are run after the edit.
- Security-sensitive changes get an extra review.
- Model routes and data sources are named before the app sends prompts.
- Agent skills and extensions are scanned before they are trusted.
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

## Repo Check Command

Run this check before trusting a patch:

```bash
python3 scripts/check_repo.py
```

The command checks:

- Python files compile
- unit tests pass
- unsafe code, secret, and PII patterns are not present in the app or helper scripts
- agent instructions and tool configs still point at the same workflow
- Codex and OpenCode model-route helpers stay repo-local under `.lab-state/`

## DefenseClaw Admission Check

Run this before trusting a new agent skill:

```bash
python3 scripts/defenseclaw_skill_demo.py
```

The demo compares one intentionally unsafe skill with one clean skill. The lesson is not that every scanner is perfect. The lesson is that agent capabilities need an admission gate before they can read files, run code, or send data away.

## Security Line

Do not let a coding agent read, print, commit, or summarize secrets. Fake samples are fine. Real tokens, cookies, cloud credentials, and private customer data are not lab material.
