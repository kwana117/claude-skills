---
name: video-analysis
description: Analyse videos in depth. Accepts URLs (YouTube, Instagram Reels, Loom, X, +1000 sites via yt-dlp) or local files. Fast mode (summary + insights) or deep mode (synchronized A/V analysis + replication guide). Runs yt-dlp/ffmpeg/Claude locally or on a configurable remote compute host via Docker. Use when the user wants to analyse videos in depth, ingest video context fast, compare videos, or generate production guides from video references.
user-invocable: true
argument-hint: <url-or-folder> [--deep] [--start MM:SS] [--end MM:SS] [--lang pt|en]
---

# Video Analysis Skill

Two modes of operation:

- **Fast Mode** (default): quick context ingestion. Synchronized frames + transcript → structured summary + insights. Ideal for second-brain feeds, content research, quick debugging of screen recordings.
- **Deep Mode** (flag `--deep`): exhaustive synchronized A/V analysis + replication guide. Runs Claude Code inside Docker with `--dangerously-skip-permissions`. Ideal for generating production guides from reference videos.

## Setup / Prerequisites

This skill needs three tools: **Docker**, **ffmpeg**, and **yt-dlp**.

- **Run locally** (simplest): install `ffmpeg` and `yt-dlp` on your machine (e.g. `brew install ffmpeg yt-dlp`). Deep mode additionally needs Docker Desktop running. With everything local you can drop the `ssh <your-compute-host>` prefix from every command below and run them directly.
- **Run on a remote compute host** (optional): if you prefer to offload the heavy lifting to another machine (more CPU/RAM, GPU, always-on box), set a `COMPUTE_HOST` you can reach over SSH and prefix the commands with `ssh "$COMPUTE_HOST"`. That host needs `ffmpeg`, `yt-dlp` and (for deep mode) Docker installed. Make sure your SSH config can reach it non-interactively.

Configure the host once, e.g.:

```bash
# Leave empty to run everything locally, or set to an SSH target you control.
COMPUTE_HOST="<your-compute-host>"   # e.g. user@host or an ssh-config alias

# Helper: run a command locally or on the remote host transparently.
run() { if [ -n "$COMPUTE_HOST" ]; then ssh "$COMPUTE_HOST" "$@"; else bash -lc "$@"; fi; }
```

In the steps below, `ssh <your-compute-host> "..."` is shorthand for "run this on the compute host (local or remote)". If you run locally, just execute the inner command directly.

**Credentials for Deep Mode:** deep mode runs Claude Code inside Docker. You must supply **your own** Claude Code credentials to the container via the `CLAUDE_CREDENTIALS_B64` environment variable (base64-encoded). Never hard-code or commit any credential value — it is always read at runtime from your environment (see Step 3 of deep mode). If a value is empty, the container will not be able to authenticate.

**Transcription fallback (optional):** if a video has no captions, you can transcribe via a Whisper API (e.g. Groq or OpenAI). Provide your own API key via an environment variable (e.g. `WHISPER_API_KEY`). Deep mode can instead run Whisper locally inside the container, so no API key is required there.

**Output:** by default, results are written to local files (next to the video or in an output folder). Saving to a note-taking system (Obsidian, etc.) is **optional** — see Step 7.

## Input parsing

`$ARGUMENTS` can be:
1. **URL** (starts with `http`) — any site supported by `yt-dlp` (YouTube, IG Reels, Loom, X, Vimeo, TikTok, etc.)
2. **Local folder path** — folder with `.mp4` files (multi-video deep mode)
3. **Local file path** — individual `.mp4`/`.mov`/`.webm`

Optional flags:
- `--deep` → enable deep mode
- `--start MM:SS` / `--end MM:SS` → analyse only a segment
- `--lang pt|en` → force transcription language (default: auto)

If `$ARGUMENTS` is empty → ask for a URL or path.

---

# FAST MODE (default)

## Step 1 — Prepare workspace on the compute host

```bash
TS=$(date +%Y%m%d-%H%M%S)
SLUG=$(echo "$INPUT" | sed 's/[^a-zA-Z0-9]/-/g' | head -c 40)
JOB=~/video-analysis/jobs/$TS-$SLUG
ssh <your-compute-host> "mkdir -p $JOB/{video,frames,audio,out}"
```

(If running locally, drop the `ssh <your-compute-host>` prefix and run the inner command directly.)

## Step 2 — Acquire video

**If URL:**

```bash
ssh <your-compute-host> "cd $JOB/video && yt-dlp \
  --no-playlist \
  --write-info-json \
  --write-auto-subs --write-subs --sub-langs 'pt,en' --sub-format 'vtt' \
  -f 'bestvideo[height<=1080]+bestaudio/best[height<=1080]' \
  -o '%(id)s.%(ext)s' \
  '$URL'"
```

Captures:
- Video (max 1080p to avoid wasting tokens on 4K frames)
- `info.json` with metadata (title, author, duration, description)
- Official subtitles (.vtt) — tries `pt` first, then `en`, then auto-generated

**If local file:** copy it into `$JOB/video/` (`scp` if the host is remote, `cp` if local) and generate a minimal `info.json` via `ffprobe`.

## Step 3 — Apply segment if requested

If `--start`/`--end` are set, trim before any processing:

```bash
ffmpeg -i input.mp4 -ss MM:SS -to MM:SS -c copy trimmed.mp4
```

## Step 4 — Frame extraction (smart cap)

Compute fps based on duration so long videos never exceed **100 frames**:

```python
duration_s = info['duration']
if duration_s <= 600:        # ≤10 min
    fps = 1                  # 1 frame/sec, max 600 frames
elif duration_s <= 1800:     # ≤30 min
    fps = 0.2                # 1 frame/5s, ~360 frames
else:                        # >30 min, hard cap 100 frames
    fps = 100 / duration_s
```

```bash
ssh <your-compute-host> "cd $JOB && ffmpeg -i video/*.mp4 -vf fps=$FPS,scale=1280:-1 frames/frame_%04d.jpg -hide_banner -loglevel error"
```

Frames always @ 1280px width — enough for Claude to see, low on tokens.

## Step 5 — Transcript (captions-first)

**Priority 1 — Official captions:**

If yt-dlp downloaded a `.vtt`, parse it to text with per-line timestamps:

```python
# Each line: "MM:SS text"
```

**Priority 2 — Whisper API (optional):**

If there are no captions, extract audio and transcribe via a Whisper API (in fast mode the local Whisper container is not running, so an API is the quick path):

```bash
ssh <your-compute-host> "cd $JOB && ffmpeg -i video/*.mp4 -vn -ar 16000 -ac 1 audio/audio.wav -hide_banner -loglevel error"
```

Then call a Whisper API (e.g. Groq or OpenAI). Provide your own API key via an environment variable, e.g.:

```bash
# Set WHISPER_API_KEY in your environment beforehand (never commit it).
curl -s https://api.groq.com/openai/v1/audio/transcriptions \
  -H "Authorization: Bearer $WHISPER_API_KEY" \
  -F model=whisper-large-v3 \
  -F file=@audio/audio.wav
```

Adjust endpoint/model for your provider of choice.

## Step 6 — Sync & analyse

Sync frames + transcript: each frame has a timestamp (frame_NNNN → second `NNNN/fps`). For each timestamp, find the matching transcript segment.

Build a markdown payload:

```markdown
## Frame @ 00:42
[image: frames/frame_0042.jpg]
**Said:** "...transcript segment for 00:42..."
```

Present it to the current Claude session (not Docker) in a single prompt with all frames + transcript. Claude analyses multimodally and produces:

1. **Executive summary** (3-5 lines)
2. **Structure** (intro/development/CTA with real timestamps)
3. **Key points** (8-15 bullets, with timestamps)
4. **Relevant visual moments** (what appears on screen that isn't spoken)
5. **Notable quotes**
6. **Practical application** (how to use this)

## Step 7 — Save outputs

**Primary output (local files):**
- `~/video-analysis/out/$SLUG.md` — full analysis (or place it next to the source video / in your chosen output folder)
- Copy of `info.json` alongside it

**Optional — save to your note-taking system (Obsidian, etc.):**

If you keep a knowledge base, also write the analysis there. Pick any destination folder you like (e.g. a "Videos Analysed" folder). Suggested frontmatter:

```yaml
---
source: {url or path}
title: {video title}
author: {channel/author}
duration: {MM:SS}
date_analyzed: {YYYY-MM-DD}
mode: rapid
tags:
  - video-analysis
  - {auto-tags by topic}
---
```

Content: the structured analysis above. This step is entirely optional — the local markdown file is the source of truth.

## Step 8 — Cleanup

- `$JOB/frames/` and `$JOB/audio/` stay on the compute host (cache for re-analysis)
- Report back: output path, duration processed, estimated cost (frames × ~$0.01)

---

# DEEP MODE (--deep)

Runs Claude Code inside Docker (on the compute host, local or remote) with `--dangerously-skip-permissions`. Extra outputs: `analysis_videoN.md`, `COMPARISON.md` (if >1 video), `REPLICATION_GUIDE.md`.

## Step 1 — Compute host structure

```bash
ssh <your-compute-host> "mkdir -p ~/video-analysis/{.devcontainer,videos,output}"
```

If input is a URL → download first via yt-dlp (Step 2 above) and copy to `videos/videoN.mp4`.
If input is a folder → copy each `.mp4` to `videos/videoN.mp4`.

## Step 2 — Docker files

### .devcontainer/Dockerfile

Base `python:3.11-slim`. Install: less, git, procps, sudo, jq, nano, vim, curl, ffmpeg, Node.js 20 (nodesource), OpenAI Whisper (`pip install openai-whisper`), Claude Code (`npm install -g @anthropic-ai/claude-code@latest`). User `node`, workdir `/workspace`.

### .devcontainer/entrypoint.sh

Decodes the `CLAUDE_CREDENTIALS_B64` env var → `~/.claude/.credentials.json` + `~/.claude/.claude.json`. The value is supplied by **you** at runtime (see Step 3); nothing is baked into the image.

### docker-compose.claude.yml

```yaml
services:
  claude:
    build:
      context: .devcontainer
      dockerfile: Dockerfile
    stdin_open: true
    tty: true
    volumes:
      - .:/app
      # Optional: mount a host Whisper model cache to avoid re-downloading.
      - ${WHISPER_CACHE:-./.whisper-cache}:/home/node/.cache/whisper:ro
    environment:
      - NODE_ENV=development
      - CLAUDE_CREDENTIALS_B64=${CLAUDE_CREDENTIALS_B64}
    deploy:
      resources:
        limits:
          memory: 12G
          cpus: "8"
    working_dir: /app
```

## Step 3 — Provide credentials and build

Supply **your own** Claude Code credentials, base64-encoded, via `CLAUDE_CREDENTIALS_B64`. How you obtain them depends on your setup (e.g. read from your local Claude config or your OS keychain). Never commit or print the value.

```bash
# Example: read your local Claude Code credentials and base64-encode them.
# Replace the source with wherever YOUR credentials live.
export CLAUDE_CREDENTIALS_B64=$(cat ~/.claude/.credentials.json | base64)

ssh <your-compute-host> "cd ~/video-analysis && CLAUDE_CREDENTIALS_B64='$CLAUDE_CREDENTIALS_B64' docker compose -f docker-compose.claude.yml build"
```

(If Docker is not on the default `PATH` over SSH, prepend the appropriate `export PATH=...` for your host.)

## Step 4 — Launch Claude inside Docker

```bash
ssh <your-compute-host> "cd ~/video-analysis && CLAUDE_CREDENTIALS_B64='$CLAUDE_CREDENTIALS_B64' docker compose -f docker-compose.claude.yml run --rm -T claude bash -c 'claude --dangerously-skip-permissions -p \"[INTERNAL_PROMPT]\" --output-format text 2>&1'"
```

Background, timeout 600000ms.

### Internal prompt — phases

**Phase 1 — Asset extraction (per video):**
1. List `/app/videos/`
2. Create `/app/output/videoN/frames/`
3. `ffmpeg -i video -vf fps=1 frames/frame_%04d.jpg`
4. `ffmpeg -i video -vn -ar 16000 -ac 1 audio.wav`
5. `whisper audio.wav --model large --language pt --output_dir ... --output_format json` (fallback `base` on OOM)

**Phase 2 — Synchronized A/V analysis (per video):**
For each transcript segment: match timestamp → corresponding frame, describe composition/colours/on-screen text/lighting, note what is said, analyse the A/V relationship (aligned, contrast, J-cut, L-cut), flag key moments.

**Phase 3 — Full structural analysis:**
Narrative structure, visual language (shot types, palette, typography, transitions, motion graphics), audio language (tone, music, sound design, pacing), A/V sync, style and identity (emotion, target, implied values, aesthetic references).

**Phase 4 — Outputs:**
- `analysis_videoN.md` — detailed analysis with concrete timestamps
- `COMPARISON.md` (if ≥2 videos) — commonalities, differences, which is more effective and why, ideal synthesis
- `REPLICATION_GUIDE.md` — timeline blueprint, production checklist, technical specs, script template, textual mood board, lessons per video

**Rule for the internal Claude:** be meticulous and specific. No generalities. Reference concrete timestamps. Describe what you see — not what you imagine.

## Step 5 — Retrieve & save

```bash
scp <your-compute-host>:~/video-analysis/output/*.md "$ORIGINAL_PATH/"
```

(If running locally, just copy from `~/video-analysis/output/`.)

Optionally also copy the outputs into your note-taking system (Obsidian, etc.) under any folder you choose.

## Step 6 — Executive summary to the user

1. Key points per analysis (with notable timestamps)
2. Main conclusions from the replication guide
3. Recommendation: which video works best as the primary reference and why
4. Top 3 immediately applicable insights

---

## Operational Notes (cross-cutting)

- `--dangerously-skip-permissions` runs **only inside the Docker container**, never on the host.
- The container is ephemeral (`--rm`) but outputs persist via the volume mount.
- Frames stay on the compute host under `~/video-analysis/jobs/$JOB/frames/` for fast re-analysis — don't delete.
- Rebuild the Docker image only when needed (check `docker images | grep claude` first).
- Whisper cache mounted read-only.
- PT content: `--language pt`. Auto-detect if language is uncertain.
- Whisper large → fallback `base` on OOM — flag it in the summary.
- If Docker is not on the SSH `PATH`, prepend the appropriate `export PATH=...` for your host.
- Recommended weekly yt-dlp upgrade (`brew upgrade yt-dlp` or your package manager's equivalent).
- For URLs that fail in yt-dlp (X.com etc.): fall back to manual download + copy.
