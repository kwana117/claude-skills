---
name: usage-tracker
description: "Track Claude Code usage credits and pace. Connects to Chrome via CDP (port 9222) to scrape claude.ai/settings/usage, extracts current usage percentages (session, weekly, extra), calculates daily budget vs ideal pace, and displays a visual dashboard with progress bars. Use when the user wants to check credits, usage, pace, or asks 'should I slow down/speed up'. Triggers: '/usage', 'check usage', 'check credits', 'how are my credits', 'usage tracker', 'pace check', 'credit pace'."
user-invocable: true
---

# Usage Tracker — Claude Credit Pace Dashboard

Track your Claude Code usage credits in real-time. Connects to a running Chrome via CDP, scrapes claude.ai/settings/usage, calculates your daily budget vs ideal pace, and tells you whether to accelerate or slow down.

## Prerequisites

- **Google Chrome** must be running with `--remote-debugging-port=9222` and logged into `claude.ai`
- User must be logged into claude.ai in that Chrome instance (login once, session persists in the user-data-dir)

By default this skill talks to a **local** Chrome on `localhost:9222`. A remote
Chrome over SSH is also supported but optional — see [Setup](#setup--one-time-per-machine).

## How It Works

### Step 1 — Extract Data via CDP

Connect to Chrome via CDP on port 9222 and navigate to the usage page. Use this Node.js script via Bash:

```bash
node -e "
const http = require('http');

function fetchURL(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let d = ''; res.on('data', c => d += c); res.on('end', () => resolve(d));
    }).on('error', reject);
  });
}

let counter = 0;
function cdpSend(ws, method, params = {}) {
  const id = ++counter;
  return new Promise((resolve) => {
    const handler = (ev) => {
      const msg = JSON.parse(ev.data || ev);
      if (msg.id === id) {
        ws.removeEventListener('message', handler);
        resolve(msg.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function run() {
  const tabs = JSON.parse(await fetchURL('http://localhost:9222/json/list'));
  const tab = tabs.find(t => t.url.includes('claude.ai'));
  if (!tab) { console.log('ERROR: No claude.ai tab found'); return; }
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = r; });
  await cdpSend(ws, 'Page.navigate', { url: 'https://claude.ai/settings/usage' });
  await new Promise(r => setTimeout(r, 6000));
  const r = await cdpSend(ws, 'Runtime.evaluate', { expression: 'document.body.innerText' });
  console.log(r.result.value);
  ws.close();
}
run().catch(console.error);
"
```

For a **remote** Chrome (optional), run the same script over SSH by prefixing it with
`ssh <your-remote-host> "export PATH=/opt/homebrew/bin:\$PATH && ..."` (adjust the
PATH to wherever `node` lives on that host).

If the script returns a login page, the user needs to log in to claude.ai in the Chrome instance first.

### Step 2 — Parse the Output

The script outputs all text from the page. Parse these values:

1. **Session usage**: Look for "X% used" after "Current session" + "Resets in Y hr Z min"
2. **Weekly All Models**: Look for "X% used" after "All models" + "Resets [Day] [Time]"
3. **Weekly Sonnet Only**: Look for "X% used" after "Sonnet only" + "Resets [Day] [Time]"
4. **Extra Usage**: Look for "€X.XX spent" + "€XX Monthly spend limit" + "€X.XX Current balance"

### Step 3 — Calculate Pace

The weekly cycle is 7 days. "Resets Wed 5:00 PM" means the NEXT Wednesday at 17:00.

**CRITICAL**: The reset day shown on the page is always the NEXT reset, NOT the previous one. Calculate correctly:

```
today = current date/time
next_reset = the NEXT occurrence of the day/time shown (e.g., next Wednesday 17:00)
  - If today is Thursday and reset is "Wed 5:00 PM", next_reset is NEXT Wednesday (6 days away)
  - If today is Wednesday 14:00 and reset is "Wed 5:00 PM", next_reset is TODAY at 17:00 (3 hours away)
  - If today is Wednesday 18:00 and reset is "Wed 5:00 PM", next_reset is NEXT Wednesday (7 days away)

days_remaining = (next_reset - today) in days (decimal)
days_elapsed = 7 - days_remaining

ideal_daily_rate = 100 / 7 = 14.29% per day
ideal_used_by_now = ideal_daily_rate * days_elapsed
actual_used = scraped percentage

difference = actual_used - ideal_used_by_now

if difference < -5:  status = "AHEAD"    (saving credits, can accelerate)
if -5 <= diff <= 5:  status = "ON TRACK" (balanced usage)
if difference > 5:   status = "BEHIND"   (over-spending, slow down)

daily_budget_remaining = (100 - actual_used) / days_remaining
```

### Step 4 — Display Visual Dashboard

Output a rich visual dashboard using Unicode block characters. This is the critical part — make it visually clear and beautiful.

**Dashboard Format:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CLAUDE USAGE DASHBOARD — [Date] [Time]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  SESSION
  [██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░] 40%
  Resets in 1h 02min

  WEEKLY — ALL MODELS                    Resets Wed 17:00
  Used   [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  6%
  Ideal  [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 20%
                                         ▲ 14% under budget

  WEEKLY — SONNET ONLY                   Resets Wed 17:00
  Used   [█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  1%
  Ideal  [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 20%
                                         ▲ 19% under budget

  EXTRA USAGE
  Spent  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%
  Budget: €0.00 / €XX.XX               Balance: €0.00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PACE ANALYSIS — WEEKLY (ALL MODELS)
  ────────────────────────────────────────────────────

  Days elapsed:     1.4 / 7
  Days remaining:   5.6

  Actual usage:     6.0%
  Ideal usage:      20.0%  (14.3%/day x 1.4 days)
  Difference:       -14.0%

  Daily budget left: 16.8%/day  (vs ideal 14.3%/day)

  ┌─────────────────────────────────────────────────┐
  │  ✅ AHEAD — You're well under budget!           │
  │                                                  │
  │  You've used only 6% in 1.4 days (4.3%/day).    │
  │  You can safely use up to 16.8%/day for the      │
  │  rest of the week. Accelerate freely!             │
  └─────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Progress Bar Rendering Rules:**

- Bar width: 40 characters
- Filled character: `█` (U+2588)
- Empty character: `░` (U+2591)
- Calculate: `filled = round(percentage / 100 * 40)`
- Always show the percentage value right-aligned after the bar
- The "Ideal" bar shows where you SHOULD be based on elapsed time
- Difference indicator:
  - Under budget: `▲` with positive message
  - Over budget: `▼` with warning message
  - On track: `●` with neutral message

**Status Messages:**

- **AHEAD** (diff < -5%): "You're well under budget! Accelerate freely."
- **ON TRACK** (-5% <= diff <= 5%): "You're on pace. Steady as she goes."
- **BEHIND** (5% < diff <= 15%): "Slightly over pace. Consider being selective with tasks."
- **CRITICAL** (diff > 15%): "Significantly over budget! Reserve remaining credits for priority tasks only."

### Step 5 — Session Info

Also note the session limit info — if session is >80%, warn that the user might hit a rate limit soon and should expect a cooldown.

## Error Handling

- If Chrome is not running on port 9222: Tell the user to launch Chrome with `--remote-debugging-port=9222`
- If no claude.ai tab found: Tell the user to open claude.ai in that Chrome instance
- If the page shows a login screen: Tell the user to log in to claude.ai in the Chrome instance
- If the reset day can't be parsed: Default to Wednesday 17:00 (standard Anthropic reset time)

## Setup — One-time per machine

### Local Chrome (default)

```bash
# Kill existing Chrome, relaunch with debugging port
killall "Google Chrome" 2>/dev/null; sleep 2
open -a "Google Chrome" --args --remote-debugging-port=9222
# Then log in to claude.ai in Chrome
```

For full control over the profile directory (recommended so it doesn't clash with
your everyday Chrome profile), launch it explicitly with a dedicated user-data-dir:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-cdp-session" \
  --no-first-run --no-default-browser-check 'https://claude.ai' &
# Then log in to claude.ai in that Chrome window
```

### Remote Chrome over SSH (optional)

If you'd rather run Chrome on another machine (e.g. an always-on box you reach over
SSH), launch it there and connect via SSH. Replace `<your-remote-host>` with your
SSH alias/host:

```bash
ssh <your-remote-host> 'killall "Google Chrome" 2>/dev/null; sleep 2 && /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-cdp-session" --no-first-run --no-default-browser-check "https://claude.ai" &'
# Then log in to claude.ai on that machine (e.g. via screen sharing / VNC)
```

Once logged in, the session persists. Chrome stays running. The skill connects via CDP each time — no new browser, no login needed.

## Usage Notes

- This skill is **read-only** — it only views the usage page, never changes settings
- The weekly reset is typically Wednesday 17:00 (user's local time)
- All calculations assume a 7-day cycle
- Extra usage tracking is informational — the pace analysis focuses on the weekly plan limits
- Can be combined with `/loop` for periodic checks (e.g., `/loop 2h /usage`)
- Works with a local Chrome (default) or a remote Chrome over SSH (optional)
