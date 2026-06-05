---
name: handoff
description: Generates a handoff.md file at the project root — a session transition document that replaces /compact when the session has accumulated bad assumptions, failed attempts, or messy debugging. Fills 6 fixed sections (Goal, Current State, Files in Flight, Changed, Failed Attempts, Next Step) from the current conversation context. Use this skill whenever the user types /handoff, "write handoff", "create handoff", "pass this to a fresh session", "handoff before leaving", or wants to hand off the current Claude Code session to a fresh agent without dragging context forward.
---

# Handoff — Claude Code Session Transition

Replaces `/compact` when the current session has accumulated cruft (bad assumptions, failed attempts, debugging loops). Instead of compacting and propagating the shape of the problem, writes `handoff.md` at the project root. In the next session (after `/clear` or a new `claude`), the first prompt is "read handoff.md and continue from the Next Step" — fresh agent, highest-performing tokens.

> Pattern derived from the Maven reel "Handoff your Claude Code session" (2026-05).

## When to run

- User typed `/handoff` or a variation (see `description`)
- The current session has **in-progress work** (not finished) that needs to continue in another session
- Critical distinction vs session-end commands:
  - Session-end skills = close the day, log completed session
  - `/handoff` = pass in-progress work to the next session (does not log anywhere, only writes the file)
  - Both can be combined: handoff first, then session-end.

## Steps

### 1. Detect the current project

Determine the project root:
1. `git rev-parse --show-toplevel 2>/dev/null` — if cwd is inside a git repo, that's the root
2. Otherwise, use the current cwd (`pwd`)
3. If the result is `~/` or `/`, **stop and ask** the user which project this is — do not write handoff to system directories

Save as `$PROJECT_ROOT`.

### 2. Check for existing handoff

```bash
test -f "$PROJECT_ROOT/handoff.md" && echo EXISTS
```

If it exists:
- Read the file
- Warn the user: "There's already a `handoff.md` for this project (session from YYYY-MM-DD HH:MM). I'll replace it."
- Don't stop — replacing is the expected behavior (one handoff per project, always the most recent).

### 3. Extract context from the current conversation

Re-read the session conversation and mentally fill the 6 sections **before** writing:

1. **Goal** — What was the declared or inferred objective of this session? 1–3 sentences. If the session started with a clear user request, paraphrase it. Include the "why" if relevant.

2. **Current State** — What's done now vs at the start of the session. Be specific. Point to files + state. Not "I'm in the middle of X" — say "X implemented and passing; Y is missing".

3. **Files in Flight** — Each file touched in this session (Edit/Write), with a short status:
   ```
   - path/to/file.ts — function X rewritten, not yet tested
   - tests/foo.test.ts — 2 new tests, 1 failing
   ```
   Exclude files only read for context. Exclude `handoff.md` itself.

4. **Changed** — High-level summary of what changed (1 sentence per area touched). Don't duplicate Files in Flight — this is narrative, that's inventory.

5. **Failed Attempts** — **The most important section.** Every attempt that failed this session. Format:
   ```
   - Tried <X> → failed because <concrete reason with evidence>
   ```
   If the session had no failures, write literally:
   ```
   - Nothing failed this session (record this anyway so the next agent knows).
   ```
   Never leave blank.

6. **Next Step** — ONE atomic, imperative, specific action. If there are multiple next steps, pick the most immediate. The others will come in the next handoff.

### 4. Determine `handoff_reason`

Infer from the conversation context. Pick one:
- `step-away` — user will be away for a few hours
- `stuck-in-loop` — session keeps trying the same thing without success (long Failed Attempts)
- `context-full` — long session, context window nearly full
- `end-of-day` — end of normal day but with work in progress
- `task-switch` — switching to another project/feature

If not obvious, ask directly: "What's the reason for the handoff? (step-away / stuck-in-loop / context-full / end-of-day / task-switch)"

### 5. Write `handoff.md`

Use Write to `$PROJECT_ROOT/handoff.md` with this exact format:

```markdown
---
project: <project name inferred from folder or project config>
session_started: <YYYY-MM-DD HH:MM> # estimate from the first turn of this session; omit if uncertain
session_ended: <YYYY-MM-DD HH:MM>   # current time (date +"%Y-%m-%d %H:%M")
handoff_reason: <reason from Step 4>
---

# Handoff — <short 1-line title summarizing the session>

## 1. Goal
<1–3 sentences>

## 2. Current State
<specific, with paths>

## 3. Files in Flight
- `<path>` — <short status>
- `<path>` — <short status>

## 4. Changed
<1 sentence per area touched>

## 5. Failed Attempts
- <attempt> → failed because <reason>
<or "Nothing failed this session.">

## 6. Next Step
<ONE imperative sentence>
```

### 6. Confirm to the user

Short response:

```
✓ handoff.md written to <$PROJECT_ROOT/handoff.md>
Reason: <handoff_reason>
Next Step: <the Next Step sentence>

Next session:
  /clear
  Read handoff.md and continue from the Next Step.
```

Do not auto-commit — the user decides whether to version it.

## Rules

- **Canonical path**: always `<project_root>/handoff.md`, never nested in `.claude/`, `docs/`, etc.
- **Replacing is OK**: one project = one handoff. If it already exists, replace it.
- **Failed Attempts never empty**: even "nothing failed" is useful information for the next agent.
- **Next Step must be atomic**: if your answer has "and then" or multiple bullets, it's not atomic yet — pick the first one.
- **No chat-style prose**: bullets and telegraphic style. The next agent wants facts, not narrative.
- **Do NOT auto-commit**: the user decides. They may explicitly ask to commit — only then do it.

## Edge Cases

### cwd is not a code project
If `pwd` is `~/`, `~/Downloads`, or a folder with no project indicators (no `.git`, no `package.json`/`pyproject.toml`/`Cargo.toml`/etc.), ask: "I can't detect a project in this directory. What's the project root?" — don't create handoff in generic directories.

### Session just started
If the current conversation has fewer than 5 significant turns, warn: "This session is too short for a useful handoff. Are you sure? (Handoff makes more sense after 1h+ of work)" — wait for confirmation.
