# KB Resolver

This folder is shared memory for any coding agent working in this repo.

## Read Order

1. Read `schema.md` to understand the note shapes.
2. Read `sessions/current-session.md` for the latest task state.
3. Read the matching project note under `projects/`.
4. Search `decisions/` and `patterns/` when the task touches a repeated choice or workflow.

## Memory Lifecycle

- Recall before rediscovery: check the KB before asking the user to repeat context.
- Update `sessions/current-session.md` when the current task state changes.
- Put durable project facts in `projects/`.
- Put choices that should survive future sessions in `decisions/`.
- Put reusable workflows or command patterns in `patterns/`.

## Rules

- Keep notes short, concrete, and easy to scan.
- Prefer updating an existing note over creating near-duplicates.
- Store evidence as commands, file paths, or short observations, not raw terminal dumps.
- Never store secrets, raw tokens, cookies, private keys, or one-time credentials.
- Record what changed and why it matters so another agent can continue without guessing.
