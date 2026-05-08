# Agent Instructions

This repo is a small DevNet training dojo for AI-assisted coding. Keep changes readable, boring, and easy to review.

## Project Map

- `dojo_app/` contains the app code.
- `tests/` contains the unit tests.
- `scripts/` contains lab helpers and quality gates.
- `docs/quality-bar.md` is the shared definition of good work.
- `.second-brain/` stores durable decisions and reusable workflow notes.

## Working Rules

- Start by reading `README.md`, this file, and `docs/quality-bar.md`.
- Prefer small patches over sweeping rewrites.
- Keep public examples free of secrets, real customer data, and private endpoints.
- Do not read `.env`, `.env.*`, or anything under `secrets/`.
- When a requirement is fuzzy, ask one focused question before changing code.
- Before handing work back, run:

```bash
python3 scripts/quality_gate.py
```

If you touched agent instructions, docs, or model routing, also run:

```bash
python3 scripts/consistency_check.py
```

If you touched code that runs commands, parses user input, or handles file paths, also run:

```bash
python3 scripts/security_review.py dojo_app scripts
```

## Definition of Done

- Unit tests pass.
- The security review passes.
- Agent instructions still match the quality bar.
- Any durable decision is recorded with `scripts/make_second_brain_note.py`.

