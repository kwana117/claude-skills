---
name: obsidian-launcher
description: Create smart launcher links for web projects that can be clicked from Obsidian notes. Generates a .command script that checks if the dev server is already running (opens browser if yes, starts server + opens browser if no). Produces a file:// link ready to paste in any Obsidian note. Use when the user wants to link a web project from Obsidian, create a launcher for a project, or make a clickable link to open a dev server.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
argument-hint: [project-path] [optional: port] [optional: obsidian-note-path]
---

# Obsidian Launcher — One-click project launchers from Obsidian notes

Creates smart `.command` scripts for macOS that launch web project dev servers and generates clickable links for Obsidian notes.

## What it does

1. Detects the project type and dev command (Vite, Next.js, Nuxt, Astro, etc.)
2. Creates a smart `.command` script in the project root that:
   - Checks if the dev server is already running on the target port
   - If running → just opens the browser
   - If not running → installs deps if needed, starts the server, waits for it, opens the browser
3. Generates an Obsidian-compatible `file://` link
4. Optionally inserts the link into a specified Obsidian note

## Step 1 — Parse arguments

The user may provide:
- **Project path** (required): absolute or relative path to the project. If not provided, use the current working directory.
- **Port** (optional): specific port to use. If not provided, detect from project config or default to 3000/5173.
- **Obsidian note path** (optional): path to an Obsidian `.md` note where the link should be inserted.

## Step 2 — Detect project type

Read the project's `package.json` to determine:

```bash
cat "$PROJECT_PATH/package.json" 2>/dev/null
```

Detection rules (check `scripts.dev` in package.json):
| Pattern in `scripts.dev` | Framework | Default port |
|---|---|---|
| `vite` | Vite | 5173 |
| `next dev` | Next.js | 3000 |
| `nuxt dev` | Nuxt | 3000 |
| `astro dev` | Astro | 4321 |
| `remix dev` | Remix | 5173 |
| `svelte` | SvelteKit | 5173 |
| `gatsby develop` | Gatsby | 8000 |
| Other/unknown | Generic | 3000 |

Also check for:
- Custom port in `vite.config.*`, `next.config.*`, etc.
- The `--port` flag in the dev script itself

If the user specified a port, always use that instead.

## Step 3 — Create the launcher script

Create `open-project.command` in the project root with this template:

```bash
#!/bin/bash
# ═══ Obsidian Launcher — PROJECT_NAME ═══
# Auto-generated smart launcher. Double-click or use Obsidian link to open.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=PORT_NUMBER
URL="http://localhost:$PORT"
DEV_CMD="DEV_COMMAND_HERE"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cd "$PROJECT_DIR" || exit 1

echo -e "${CYAN}═══ Obsidian Launcher ═══${NC}"
echo -e "Project: ${GREEN}$(basename "$PROJECT_DIR")${NC}"
echo ""

# Check if server is already running on this port
if lsof -i :"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo -e "${GREEN}✓ Server already running on port $PORT${NC}"
  echo -e "  Opening browser..."
  open "$URL"
  exit 0
fi

echo -e "${YELLOW}Starting dev server on port $PORT...${NC}"

# Install dependencies if node_modules is missing or outdated
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
  echo -e "${CYAN}Installing dependencies...${NC}"
  npm install --silent 2>/dev/null
fi

# Start dev server in background
$DEV_CMD &
SERVER_PID=$!

# Wait for server to be ready (max 30 seconds)
echo -n "Waiting for server"
for i in $(seq 1 60); do
  if lsof -i :"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}✓ Server ready!${NC}"
    open "$URL"
    echo -e "  PID: $SERVER_PID"
    echo -e "  URL: $URL"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop the server.${NC}"
    wait $SERVER_PID
    exit 0
  fi
  echo -n "."
  sleep 0.5
done

echo ""
echo -e "${YELLOW}⚠ Server didn't start within 30s. Check for errors above.${NC}"
wait $SERVER_PID
```

**IMPORTANT replacements:**
- `PROJECT_NAME` → basename of the project directory
- `PORT_NUMBER` → detected or user-specified port
- `DEV_COMMAND_HERE` → the actual dev command, e.g., `npx vite --port 5173` or `npx next dev -p 3000`

Make the script executable:
```bash
chmod +x "$PROJECT_PATH/open-project.command"
```

## Step 4 — Generate the Obsidian link

The link format for Obsidian is:

```
[Abrir PROJECT_NAME](file://ENCODED_PATH_TO_COMMAND_FILE)
```

URL-encode the full path (spaces → `%20`, special chars encoded). Use this bash to generate:

```bash
python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe='/'))" "$PROJECT_PATH/open-project.command"
```

## Step 5 — Insert into Obsidian note (if path provided)

If the user specified an Obsidian note path:

1. Read the note
2. Insert the link as a blockquote right after the first H1 heading:

```markdown
> **[Abrir PROJECT_NAME](file://ENCODED_PATH)** — clica para abrir o dashboard no browser.
```

If no H1 is found, insert at the top of the file.

If no Obsidian note path is provided, just output the link to the user so they can copy-paste it.

## Step 6 — Verify

Test that the script is valid:
```bash
bash -n "$PROJECT_PATH/open-project.command"
```

## Output

Always show the user:
1. The framework detected and port chosen
2. The path to the `.command` file
3. The Obsidian-ready link (in a code block so they can copy it)
4. Instructions: "Double-click the .command file no Finder, ou clica no link no Obsidian."

## Updating existing launchers

If `open-project.command` already exists in the project, read it first and ask the user if they want to overwrite or update the port/command.

## Notes

- The `.command` extension is macOS-specific — Terminal.app opens it automatically on double-click
- The `file://` protocol works in Obsidian's reading view (not editing view)
- If the project uses pnpm or yarn, detect from lockfiles and adjust the install/dev commands accordingly
- Always use `npx`/`pnpx`/`yarn` prefix for the dev command to avoid global dependency issues
