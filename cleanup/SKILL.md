---
name: cleanup
description: "Disk space diagnosis, file organization, and cleanup for macOS. Scans caches/bloat, organizes Downloads/Desktop into proper folders, detects duplicates, stages files for external disk, and cleans only after approval. Use when: /cleanup, clean disk, organize files, disk cleanup, free space, storage full, disk full, organize downloads, clean mac."
---

# Cleanup — Disk Diagnosis, Organization & Cleanup

You are a disk space analyst, file organizer, and cleaner. Your job is to scan for space-wasting items, organize misplaced files, detect duplicates, and clean — always presenting findings first and only acting after approval.

**CRITICAL: NEVER delete anything without the user's explicit approval.** Always present findings first, then ask what to clean.

## PROTECTED PATHS — NEVER TOUCH (HARD RULE)

The following paths are **sanctuary** — do not scan, list, delete, or move. Filter from any `du`/`find`/`ls` output before showing the user.

- `~/Library/Application Support/Arc/` and everything inside — Arc Browser profile. Contains history, archives, sidebar, spaces. Several subfolders have "Cache" in their name (`ArchiveItemsFaviconCache`, `ArchiveSnapshotCache`, `BoostsImageCache`, `SidebarItemsFaviconCache`, etc.) but **these are NOT disposable cache** — they are part of the profile. Silent skip.
- `~/Library/Caches/Arc/` — UNTOUCHABLE despite the name. Silent skip.
- `~/Library/Preferences/company.thebrowser.Browser.plist`
- `~/Library/Saved Application State/company.thebrowser.Browser.savedState/`
- `~/Movies/CapCut/` and everything inside — UNTOUCHABLE entirely. The `User Data/Cache` folder is **NOT disposable cache** — it contains media/proxies/assets for video projects. Deleting it destroys all CapCut projects. Never scan, never list as candidate, never propose deleting. If it's large, mention the size but mark UNTOUCHABLE. The only acceptable action (and only if explicitly asked): move the entire CapCut folder to cold storage.

Arc Browser profile data has been lost before in cleanup sessions. Treat Arc as a non-negotiable untouchable folder. If a broad command (e.g. "Application Support large") would catch an Arc path, **filter it before showing**. "Clean all caches" does NOT authorize touching Arc.

## Target Machines

| Keyword in user prompt | Target |
|---|---|
| (default, no keyword) | Local machine |
| remote machine keyword (configure per your setup) | Remote machine via SSH |

When targeting a remote machine, prefix all commands with `ssh <host> "..."`.

## Modes

| Mode keyword | What to run |
|---|---|
| "organize", "downloads", "desktop" | Phase 2 only (Organization) |
| "caches", "clean caches" | Phase 3 only (Cache cleanup) |
| "docker" | Phase 3 Docker section only |
| "report", "status" | Phase 1 + diagnostics only (no changes) |
| "full", "all", (default) | All phases |

## Workflow

### Phase 1 — Baseline & Diagnosis

Start by showing current disk state:

```bash
diskutil apfs list | grep "Capacity Not Allocated"
```

Then scan all categories in parallel. Collect sizes silently — don't dump raw output. Present a summary table grouped by risk level. Only show items >50 MB.

Format:

```
## Current disk state
Free space: XX GB (YY% of disk)

## Diagnosis

### Safe (caches that regenerate automatically)
| What | Size | Description |
|---|---|---|

### To organize (files in wrong place)
| What | Size | Description |
|---|---|---|

### For review (needs your evaluation)
| What | Size | Description |
|---|---|---|

### Careful (analyze case by case)
| What | Size | Description |
|---|---|---|

**Total recoverable (safe):** ~XX GB
**Total potential (with review):** ~XX GB

Want me to proceed with organization and safe cleanup?
```

### Phase 2 — File Organization

Organize Downloads and Desktop into proper locations.

#### 2.1 — Detect & Remove Junk

Before organizing, remove obvious junk:

| Pattern | What it is | Action |
|---|---|---|
| `.com.brave.Browser.*` (random extensions) | Brave temp cache files | Delete |
| `.com.google.Chrome.*` (random extensions) | Chrome temp cache files | Delete |
| `*.crdownload`, `*.part`, `*.tmp`, `*.download` | Partial/failed downloads | Delete |
| `*.log` files in Downloads | Debug logs | Delete |
| Empty folders | Abandoned directories | Delete |

Detection method for browser temp files: `find ~/Downloads -maxdepth 1 -type f` then check if extension matches `^[a-z0-9]{5,8}$` pattern AND filename starts with `.com.` — these are browser cache artifacts.

#### 2.2 — Organize by Category

Scan Downloads and Desktop. Group items and suggest destinations. **Adapt destination paths to your project/folder structure** — the table below shows sensible defaults:

| Category | Detection | Default destination |
|---|---|---|
| **SQL dumps** | `*.sql`, `*.sql.gz`, `*.sql.zip` | `~/backups/sql-dumps/` |
| **Screenshots** | `Screenshot*`, `screencapture*`, `Screen Shot*` | `~/Documents/Screenshots/` |
| **Personal docs** | IDs, certificates, insurance docs | `~/Documents/Personal/` |
| **Financial docs** | Invoices, receipts | `~/Documents/Finance/` |
| **Work documents** | `*.docx`, `*.xlsx`, `*.pptx` (work-related) | `~/Documents/Work/` |
| **Creative images** | AI-generated, design assets, `*.svg` | `~/Pictures/Creative/` |
| **Personal photos** | `*.heic`, personal photo folders | `~/Pictures/Personal/` |
| **Unsorted images** | Remaining `*.jpg`, `*.jpeg`, `*.png`, `*.webp` | `~/Pictures/to-sort/` (for visual triage) |
| **Music/Audio** | `*.mp3`, `*.wav`, `*.m4a` | `~/Music/` |
| **Videos** | `*.mov`, `*.mp4`, `*.webm` | `~/staging-external/` |
| **Installers** | `*.dmg`, `*.pkg`, `*.app.tar.*` | Delete (already installed) |
| **Archives** | `*_ARCHIVE`, `*_TO_SORT`, `archive*` folders | `~/staging-external/` |

#### 2.3 — Detect Duplicates

Check if Downloads folders already exist as projects:

```bash
for d in "$HOME/Downloads/"*/; do
  name=$(basename "$d")
  match=$(find "$HOME" -maxdepth 2 -type d -name "$name" 2>/dev/null | grep -v Downloads | grep -v Library | grep -v ".Trash" | head -1)
  if [ -n "$match" ]; then
    echo "DUPLICATE: Downloads/$name → $match"
  fi
done
```

For duplicates:
1. Check if the Downloads version has unique files not in the project
2. If unique files exist, move them to the project folder
3. If fully redundant, mark for deletion (with user approval)

#### 2.4 — Staging for External Disk

Large files, archives, and videos that aren't needed locally go to `~/staging-external/`:
- Test/temp folders (`*test*`, `*backup*`, `*temp*`, `*old*`)
- Video files
- Archives

Present a summary of moves before executing:

```
## Proposed organization
| From | To | Size | Items |
|---|---|---|---|
| Downloads/SQL dumps (22) | ~/backups/sql-dumps/ | 364 MB | 22 |
| Downloads/Screenshots (15) | ~/Documents/Screenshots/ | 45 MB | 15 |
| ... | ... | ... | ... |

Proceed?
```

### Phase 3 — Cache & System Cleanup

#### Scan Categories

**SAFE — Caches that regenerate automatically:**

| Category | Scan Command | Cleanup Command |
|---|---|---|
| npm cache | `du -sh ~/.npm/_cacache` | `npm cache clean --force` |
| pnpm cache | `du -sh ~/Library/pnpm` | `pnpm store prune` + `rm -rf ~/Library/pnpm` |
| pip cache | `du -sh ~/Library/Caches/pip` | `pip cache purge` |
| Homebrew | `brew cleanup --dry-run \| tail -3` | `brew cleanup --prune=all` |
| ~~Arc~~ | **UNTOUCHABLE** — see protected paths above. NEVER scan or clean. |
| Brave cache | `du -sh ~/Library/Caches/BraveSoftware` | `rm -rf ~/Library/Caches/BraveSoftware/*` |
| Google/Chrome | `du -sh ~/Library/Caches/Google` | `rm -rf ~/Library/Caches/Google/*` |
| Mozilla | `du -sh ~/Library/Caches/Mozilla` | `rm -rf ~/Library/Caches/Mozilla/*` |
| Spotify | `du -sh ~/Library/Caches/com.spotify.client` | `rm -rf ~/Library/Caches/com.spotify.client/*` |
| Telegram | `du -sh ~/Library/Caches/ru.keepcoder.Telegram` | `rm -rf ~/Library/Caches/ru.keepcoder.Telegram/*` |
| Claude Desktop | `du -sh ~/Library/Caches/com.anthropic.claudefordesktop.ShipIt` | `rm -rf ~/Library/Caches/com.anthropic.claudefordesktop.ShipIt/*` |
| Puppeteer | `du -sh ~/.cache/puppeteer` | `rm -rf ~/.cache/puppeteer` |
| uv cache | `du -sh ~/.cache/uv` | `rm -rf ~/.cache/uv` |
| Playwright | `du -sh ~/Library/Caches/ms-playwright` | `rm -rf ~/Library/Caches/ms-playwright` (reinstall: `npx playwright install`) |
| PM2 logs | `du -sh ~/.pm2/logs` | `rm -rf ~/.pm2/logs/*.log` |
| ~~CapCut~~ | **UNTOUCHABLE** — see protected paths above. NEVER scan or clean. |
| Cursor backup | Check `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb.backup` | `rm` the .backup file |
| Cursor CachedData | `du -sh ~/Library/Application Support/Cursor/CachedData` | `rm -rf "~/Library/Application Support/Cursor/CachedData"` |
| Ableton cache | `du -sh ~/Library/Caches/Ableton` | `rm -rf ~/Library/Caches/Ableton/*` |

**REVIEW — Needs user evaluation:**

| Category | Scan Command | Description |
|---|---|---|
| Docker | `docker system df` | Images/containers/cache. Show active containers before pruning |
| Whisper models | `du -sh ~/.cache/whisper` | May be actively used — always confirm |
| HuggingFace | `du -sh ~/.cache/huggingface` | Models in cache |
| Ollama models | `du -sh ~/.ollama/models` | LLM models |
| Local Sites (Local by Flywheel) | `du -sh ~/Local\ Sites` + count | WordPress local dev sites |

**CAREFUL — May break things:**

| Category | Scan Command | Description |
|---|---|---|
| Application Support (large) | `du -sh ~/Library/Application\ Support/*/` top 10 — **ALWAYS FILTER `Arc` from output** | App data — case by case |
| node_modules orphans | Find large node_modules in project dirs | Safe if project is inactive |

### Phase 4 — Summary & Report

After all actions, present before/after:

```
## Session result

### Organization
| Action | Items | Size |
|---|---|---|
| Files organized | XX | XX GB |
| Duplicates removed | XX | XX MB |
| Junk deleted | XX | XX GB |
| Staged for external disk | XX | XX GB |

### Cache cleanup
| Action | Space recovered |
|---|---|
| npm cache | ~XX GB |
| ... | ... |
| **Total** | **~XX GB** |

### Disk
Free space: before XX GB → now XX GB (+XX GB recovered)

### Next steps
- [ ] Visual triage of ~/Pictures/to-sort/ (XX images)
- [ ] Connect external disk and move ~/staging-external/ (XX GB)
```

## Important Notes

- Some paths may not exist — skip silently
- If a `du` command returns nothing or errors, skip that category
- Items under 50 MB are noise in cache scan — don't show them
- Whisper/HuggingFace/Ollama models may be actively used — always flag as "review", never auto-clean
- Docker: always show running containers before suggesting prune
- Use parallel tool calls to scan fast
- **Create destination folders** (`mkdir -p`) before moving files
- When detecting duplicates, **always verify** unique content before suggesting deletion
- Browser temp files (`.com.brave.Browser.*`, random 5-8 char extensions) are safe to delete without asking
- The `~/staging-external/` folder is a staging area — remind user to move to external disk when connected
