---
name: session-summary
description: Summarizes what was done in the current conversation session in 2-4 sentences, in Portuguese (PT-PT). Use this skill whenever the user types /session-summary, "resume a sessão", "o que fizemos", "resume o que foi feito", or asks for a summary of the current session's work.
---

# Session Summary

Read the conversation history up to this point and write a concise summary of what was accomplished.

## Rules

- 2 to 4 sentences maximum — no more
- Portuguese (PT-PT) only
- No bullet points, no headers, no lists — plain paragraph
- Factual and direct: what was done, not what was discussed or planned
- Focus on concrete outcomes (files created, bugs fixed, features built, tasks completed)
- Skip meta-conversation (questions asked, options considered) unless nothing concrete was done
- If nothing concrete was done yet, say so in one sentence

## Output

Just the paragraph. No preamble like "Aqui está o resumo:" — go straight to the summary.
