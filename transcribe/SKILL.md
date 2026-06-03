---
name: transcribe
description: Transcribe audio or video files. Two methods: local Whisper (default, free, runs on your machine), or OpenAI Whisper API (faster, needs OPENAI_API_KEY). Use when the user asks to transcribe audio, video, podcasts, interviews, or any media with speech.
user-invocable: true
argument-hint: [path-to-file] [local|api]
---

# Transcribe Skill

Transcribes audio/video files using one of two methods:
- **local** (default) — OpenAI Whisper running on your machine. Free, slower, great quality for many languages. Can optionally run on a remote host over SSH.
- **api** — OpenAI Whisper API (`whisper-1`). Fast, uses `OPENAI_API_KEY`.

## Input parsing

$ARGUMENTS may contain up to two parts: `[filepath] [method]`

- Parse the **last word** of $ARGUMENTS. If it is `local` or `api`, that is the method; the rest is the file path.
- If method is not specified, default to `local`.
- Examples:
  - `/transcribe interview.mp3` → file=interview.mp3, method=local
  - `/transcribe interview.mp3 api` → file=interview.mp3, method=api
  - `/transcribe interview.mp3 local` → file=interview.mp3, method=local

If no file path is present after parsing, ask the user for the file path.

Supported formats: `.mp3`, `.m4a`, `.wav`, `.ogg`, `.flac`, `.aac`, `.wma`, `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`

## Step 1 — Validate input

Check the file exists and show basic info:

```bash
ls -lh "FILEPATH"
```

If the file doesn't exist, tell the user and stop.

## Step 2 — Ask for language (if not obvious)

If the user mentioned the language, use that. Common options:
- `en` — English
- `pt` — Portuguese
- `es` — Spanish
- `auto` — auto-detect (mixed languages)

If unsure, ask the user, or use `auto` to let Whisper detect the language.

---

## Method: local (Whisper on your machine)

By default this runs **locally**. It can optionally run on a remote host over SSH (see "Running on a remote host" below).

**Prerequisites:**
- OpenAI Whisper installed: `pip install -U openai-whisper` (verify with `python3 -m whisper --help`)
- FFmpeg installed and on your `PATH` (e.g. `brew install ffmpeg` on macOS, or your distro's package manager)

The first run of a model will download its weights. The `large` model gives the best quality; use `medium`/`small`/`base` for less memory or faster runs.

### Step 3.5L — Convert to WAV

Whisper works best with WAV input. Always convert:

```bash
ffmpeg -i "FILEPATH" -ar 16000 -ac 1 -c:a pcm_s16le "FILEPATH_WITHOUT_EXT.wav" -y
```

### Step 4L — Transcribe

```bash
python3 -m whisper "FILEPATH_WITHOUT_EXT.wav" --model large --language LANG --output_dir "LOCAL_OUTPUT_DIR" --output_format txt
```

For `auto` language detection, omit the `--language` flag.

Run with timeout up to 600000ms — the `large` model takes roughly ~4x realtime on CPU.

### Step 5L — Locate transcript

The transcript is written to `LOCAL_OUTPUT_DIR/FILENAME_WITHOUT_EXT.txt`. Place it in the same directory as the original file.

### Running on a remote host (optional)

If you prefer to offload transcription to a more powerful machine, you can run the same steps over SSH. Replace `<your-remote-host>` with your SSH host (as configured in `~/.ssh/config` or `user@hostname`):

```bash
# 1. Send the file
scp "FILEPATH" <your-remote-host>:/tmp/

# 2. Convert to WAV on the remote host
ssh <your-remote-host> "ffmpeg -i '/tmp/FILENAME' -ar 16000 -ac 1 -c:a pcm_s16le '/tmp/FILENAME_WITHOUT_EXT.wav' -y"

# 3. Transcribe on the remote host
ssh <your-remote-host> "python3 -m whisper '/tmp/FILENAME_WITHOUT_EXT.wav' --model large --language LANG --output_dir /tmp/ --output_format txt"

# 4. Retrieve the transcript
scp <your-remote-host>:/tmp/FILENAME_WITHOUT_EXT.txt "LOCAL_OUTPUT_DIR/"

# 5. Clean up the remote host
ssh <your-remote-host> "rm -f '/tmp/FILENAME' '/tmp/FILENAME_WITHOUT_EXT.wav' '/tmp/FILENAME_WITHOUT_EXT.txt'"
```

If `ffmpeg` or `whisper` are installed in a non-default location on the remote host, prepend the appropriate directory to `PATH` inside the SSH command (e.g. `export PATH=/path/to/bin:$PATH && ...`).

---

## Method: api (OpenAI Whisper API)

**Prerequisites:**
- An OpenAI API key available in the `OPENAI_API_KEY` environment variable.
- If you keep it in a secrets manager (e.g. a password manager, `pass`, your OS keychain, a `.env` file), read it from there and export it before running:

```bash
export OPENAI_API_KEY="sk-..."   # or load it from your secrets manager
```

If `OPENAI_API_KEY` is not set, ask the user to provide it (or to set it in their secrets manager) before continuing. Never hard-code or print the key.

### Step 3A — Call Whisper API

The file must be ≤ 25MB. If larger, warn the user and suggest splitting or using the `local` method instead.

```bash
curl -s https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F file="@FILEPATH" \
  -F model="whisper-1" \
  -F language="LANG" \
  -F response_format="text"
```

For `auto` language detection, omit the `-F language` parameter.

### Step 4A — Save transcript

Save the API response (plain text) to a `.txt` file alongside the original:

```
FILEPATH_WITHOUT_EXT.txt
```

---

## Step 7 — Show result (both methods)

1. Read the transcript file and show a preview (first ~30 lines)
2. Report: file path of the saved transcript, approximate word count, method used
3. Ask if the user wants the full transcript displayed or any post-processing (summary, translation, formatting, etc.)

## Notes

- **local**: ensure `ffmpeg` and `whisper` are on your `PATH` before running
- **local**: if whisper fails with memory errors on the `large` model, retry with `medium` (or `small`) and warn the user
- **local**: for very large files (> 500MB) sent to a remote host, warn the user that the SCP transfer may take a while
- **api**: 25MB limit — suggest `local` for larger files
- **api**: read the key from `OPENAI_API_KEY` (or from your secrets manager); never expose it in logs or responses
