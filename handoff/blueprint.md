# `handoff.md` — Blueprint

> Session transition document for Claude Code. Replaces `/compact` when the session has started accumulating bad assumptions, failed attempts, or messy debugging loops. Gives the next agent the **highest-performing tokens** possible: clean context, explicit priorities, zero baggage.
>
> **Principle**: each Claude turn starts with the best possible context. Not a "continuation" — a **fresh, informed start**.

---

## Canonical Format (6 sections, fixed order)

```markdown
---
project: <project name>
session_started: <YYYY-MM-DD HH:MM>
session_ended: <YYYY-MM-DD HH:MM>
handoff_reason: <step-away | stuck-in-loop | context-full | end-of-day | task-switch>
---

# Handoff — <short title, 1 line>

## 1. Goal
> What we're trying to build. 1–3 sentences. Include the "why" if not obvious from the code.

## 2. Current State
> Where the work stands now. Specific. Point to files and lines if relevant.
> Avoid "I'm in the middle of X" — say "X is implemented and passing; Y is missing".

## 3. Files in Flight
> List of active files in this session. Each line: `path — status`.
> - `src/auth/middleware.ts` — refactor in progress, `validateToken` rewritten but not tested
> - `tests/auth.test.ts` — 3 new tests, 1 failing (line 47)

## 4. Changed
> What was touched this session (regardless of commit status).
> Useful for the next agent to know what does NOT need to be re-read from scratch.

## 5. Failed Attempts
> Things that were tried and did NOT work. Each item: attempt + reason for failure + evidence.
> This section is the most important — it prevents the next agent from repeating the same loop.
> - Tried using `jose` for JWT verification → fails because the token uses non-standard HS512
> - Tried mocking `redis-client` in tests → mock doesn't capture `pipeline()`, switching to `ioredis-mock`

## 6. Next Step
> The next concrete action. ONE sentence. Imperative.
> "Implement `validateToken` with `jsonwebtoken` instead of `jose`."
> NOT "continue working on auth" — specific and atomic.
```

---

## Quality Rules

1. **Specificity bomb** — real names (files, functions, errors), not placeholders. Like `Assumed userId was string`, `Tried three failed migrations`, `Hallucinated import path`.
2. **Failed Attempts is mandatory** — even if "nothing failed yet". It's the section that creates the most value for the next agent.
3. **Next Step = 1 atomic action** — if there are 3 next steps, pick the first. The others go in the next session's handoff.
4. **No chat-style prose** — bullets and telegraphic style. The next agent doesn't need "we successfully managed to refactor"; it needs "validateToken: passes, refresh: TODO".
5. **Versionable** — `handoff.md` is commit-worthy. Allows handoff history and sharing across machines.
6. **Canonical path** — always at the project root: `<project>/handoff.md`. One per project, overwritten between sessions.

---

## How to Use (full workflow)

### A. End the current session
1. Ask Claude: `write handoff.md` (or run the `/handoff` skill).
2. Review the 6 sections — correct anything vague.
3. (Optional) Commit: `git add handoff.md && git commit -m "handoff: <title>"`.

### B. Clear context
- For an immediate reset in the same terminal: `/clear`.
- To open a new Claude session in the same folder: open a new terminal and run `claude`.

### C. Resume
First prompt of the new session:
```
Read handoff.md and continue from the Next Step.
```

Nothing more. The new agent has a clean context window + curated handoff = highest-performing tokens.

---

## When to Use

| Situation | Use handoff? |
|---|---|
| Stepping away for a few hours | ✅ Yes |
| Claude is looping on the same solution | ✅ Yes (most important case) |
| Context window near 80% | ✅ Yes |
| Switching feature/project mid-session | ✅ Yes |
| About to commit and close the laptop | ✅ Yes |
| 20-min session, everything went smoothly | ❌ Not needed |
| Normal end-of-day with work complete | ❌ Session-end logging covers it — only use handoff if there's work **in progress** |

---

## Anti-patterns

- ❌ "Continued the refactor — see what's done and follow up" (vague, forces the next agent to investigate)
- ❌ Empty Failed Attempts when there were loops (loses the main value)
- ❌ Next Step with 5 bullets (pick one)
- ❌ Saving handoff inside `.claude/` or nested folders — always at the project root
- ❌ Compacting **and then** writing handoff — `/compact` already corrupted the context; do handoff **before** any compaction

---

## Reference

Pattern derived from the Maven reel "Handoff your Claude Code session" (2026-05).
