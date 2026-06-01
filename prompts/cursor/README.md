# Cursor Agent Handoff System

This directory contains the structured prompt-based workflow for directing **Cursor** (as a senior developer agent).

## Quick Overview

- **next/**: New tasks ready for Cursor to pick up.
- **in-progress/**: Tasks currently being worked on (claimed by moving from `next/`).
- **done/**: Completed tasks with full artifacts (original prompt, Cursor's output, and review notes).

## How to Use

Simply open Cursor and say one of the following:

- "Work on the next task."
- "Pick up the next available prompt."
- "Start the next task in the queue."

Cursor will automatically:
1. Find the oldest task in `next/`.
2. Claim it by moving it to `in-progress/`.
3. Execute the work.
4. Deliver results under `done/`.

## Full Documentation

See `WORKFLOW.md` in this directory for the complete protocol, including:
- How to create new tasks
- Claiming and completion rules
- Parallel agent safety
- Review process
- Scope discipline guidelines

## Reorganization Note

As of June 2025, this system was moved under `prompts/cursor/` for better organization (previously lived at the top level of `prompts/`). Historical task records may contain older path references.