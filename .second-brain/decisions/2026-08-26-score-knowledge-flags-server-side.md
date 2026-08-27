---
type: decision
status: active
---

# Score Knowledge Flags on the Leaderboard

## Decision

Keep knowledge-flag answer keys and scoring on the leaderboard service. The Dojo CLI shows six choices and submits one normalized answer with a unique attempt ID. Each submitted wrong answer removes 2 points from that flag, down to 0; invalid terminal input is not submitted.

## Why It Matters

Participants must inspect the lab files instead of finding an answer key in the learner repo. Attempt IDs also make a retried network request safe without changing the rule that every intentional wrong answer costs points.

## Evidence

- `dojo capture map-second-brain`
- `dojo capture trace-defense-evidence`
- `dojo challenges`
- `python3 scripts/check_repo.py`
