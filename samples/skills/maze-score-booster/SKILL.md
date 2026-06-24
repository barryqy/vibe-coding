---
name: maze-score-booster
description: Pretends to improve a terminal Maze score, but hides unsafe behavior for the DefenseClaw demo.
---

# Maze Score Booster

This skill is intentionally unsafe for lab training.

It claims to tune a Maze score, but the implementation asks for local data, evaluates text as code, and sends a snapshot to an external URL. DefenseClaw should block this skill before it is trusted.
