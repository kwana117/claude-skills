# Claude Code Skills

A collection of [Claude Code](https://claude.com/claude-code) skills I built and use day-to-day, cleaned up for sharing. Each skill is a self-contained folder with a `SKILL.md` (instructions Claude reads) plus any helper scripts/templates.

> Some skills produce **Portuguese (PT-PT)** output by default — that's just my working language. It's easy to change in each `SKILL.md`.

## Skills

| Skill | What it does |
|---|---|
| [`proof`](proof) | Generates visual proof of changes (HTML page or captioned PNGs) so you can validate work before showing a client. Screenshots + "request / what was done / what to approve". |
| [`one-pager`](one-pager) | Creates a polished single-file HTML page (pitch, status report, roadmap, explainer…) from a set of style templates, ready to deploy to any host. |
| [`carousel`](carousel) | Generates Instagram carousels (1080×1350 PNG) via a 3-agent pipeline (plan → render → review-until-pass). |
| [`classifier-dashboard`](classifier-dashboard) | Builds an interactive drag-and-drop dashboard to triage large lists of items into buckets. |
| [`transcribe`](transcribe) | Transcribes audio/video — local Whisper or the OpenAI API. |
| [`video-analysis`](video-analysis) | Deep video analysis (yt-dlp + ffmpeg + Claude in Docker), locally or on a remote compute host. |
| [`web-image-optimizer`](web-image-optimizer) | Optimizes images for the web — convert, resize, compress, sequential rename. |
| [`usage-tracker`](usage-tracker) | Tracks Claude Code usage/credits and pace by reading the usage page over Chrome DevTools Protocol. |
| [`session-summary`](session-summary) | Summarizes what was done in the current Claude Code session. |
| [`obsidian-launcher`](obsidian-launcher) | Creates clickable launcher links to start a project's dev server straight from an Obsidian note. |

## Install

Skills live in `~/.claude/skills/`. To install one:

```bash
# clone, then copy the skills you want
git clone https://github.com/kwana117/claude-skills.git
cp -R claude-skills/proof ~/.claude/skills/
```

Restart Claude Code (or start a new session) and the skill becomes available — invoke it with `/proof`, `/one-pager`, etc., or just describe the task and Claude will pick it up.

## Notes

- Some skills depend on external tools or services — for example `transcribe` (Whisper / OpenAI API), `carousel` (Playwright/Chromium), `usage-tracker` (Chrome with `--remote-debugging-port`), `video-analysis` (Docker, ffmpeg, yt-dlp). Each `SKILL.md` lists its own prerequisites and setup.
- Any deploy/host/server steps use placeholders (`<your-server>`, `<your-domain>`) — point them at your own infrastructure.
- API keys are always read from environment variables — never hard-code secrets.

## License

[MIT](LICENSE) — use, modify and share freely.
