# Quality Bar

Good vibe coding still has a quality bar.

## What Good Looks Like

- The task is small enough to review.
- The agent has project context before it edits.
- The agent searches `.second-brain/` for notes that match the task before continuing work.
- The agent updates `.second-brain/sessions/current-session.md` as normal task housekeeping when state changes.
- Tests and checks are run after the edit.
- Security-sensitive changes get an extra review.
- Model routes and data sources are named before the app sends prompts.
- Local MCP tools are called through an explicit client before they are treated as trusted context.
- Repo-local skills are installed from known files and checked before their artifacts are trusted.
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

## Second Brain

Use `.second-brain/` when work moves across tools or sessions.

- `RESOLVER.md` tells the agent how to resolve relevant notes.
- `schema.md` keeps notes predictable.
- `projects/` holds durable project context.
- `sessions/current-session.md` holds current state, recent work, open questions, boundaries, and verification.
- `patterns/` holds reusable workflows or command patterns.
- `decisions/` holds choices that should survive the lab.

Do not put secrets, raw tokens, cookies, or private keys in memory.
Treat session-note updates as part of finishing the work.

## Repo Check Command

Run this check before trusting a patch:

```bash
python3 scripts/check_repo.py
```

The command checks:

- Python files compile
- unit tests pass
- unsafe code and secret-shaped patterns are not present in the normal app or helper paths
- agent instructions and tool configs still point at the same workflow
- Codex and OpenCode model-route helpers stay repo-local under `.lab-state/`
- the safe BarryFlights status path can be called without personal credentials

## DefenseClaw Admission Check

Run these before trusting new agent capabilities:

```bash
python3 scripts/defenseclaw_skill_demo.py
python3 scripts/defenseclaw_mcp_demo.py
```

The demos compare clean and intentionally unsafe Skills and MCP servers. The lesson is not that every scanner is perfect. The lesson is that agent capabilities need an admission gate before they can read files, run code, or send data away.

## Security Line

Do not let a coding agent read, print, commit, or summarize secrets. Purpose-built sample values are fine. Real tokens, cookies, private keys, cloud credentials, and private customer data are not lab material.
