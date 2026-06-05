---
name: decisions
description: Generate an interactive decisions page (HTML + JS) where each decision presents a Recommendation vs Alternative as clickable options, plus a free-text "Other choice". The page tracks selections in localStorage, shows live progress (X/N decisions), and produces a copy-to-clipboard summary. Saves locally and opens in browser. Use when the user says /decisions, "make a decisions page", "interactive page to decide X", "I want to decide Y with clicks", or asks for a structured decision-making page they can fill in interactively and copy the result.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: [topic] [--slug=custom-slug] [--to=recipient]
---

# Decisions — Interactive decision page generator

Generates a single-file HTML page with a list of decisions (each with Recommendation / Alternative / Other choice clickable options), a sticky progress bar, and a copy-to-clipboard summary panel. Saves to `/tmp/decisions/<slug>/index.html` and opens in the browser.

## The pattern

A structured decision page where each card has:
- A clear **Recommendation** with supporting bullet points
- A serious **Alternative** (or multiple alternatives) with bullet points
- A **Tradeoff** — what you lose by picking the recommendation
- A free-text **"Other choice"** textarea (auto-injected by JS)

The page generates a copyable summary of all selections when the user is done.

## Visual palette

- Background: parchment `#F5F1EB`
- Accent: burnt orange `#CC785C`
- Fonts: Inter (body), JetBrains Mono (code/labels)
- Status chips: rose (decide first), amber (important), green (validated), muted (can wait)

## Step 1 — Gather inputs

Required:
- **Topic** — what is being decided (e.g. "project stack", "MVP scope", "legal structure"). Infer from conversation if possible.
- **Decisions** — array of decision items. Each has:
  - `num` — short ID (e.g. "#1", "#2"…)
  - `title` — what the decision is about
  - `phase` — optional grouping (Phase A · Now / Phase B · 2 weeks / Phase C · Post-validation) — only use if there's a real dependency order
  - `status_chip` — one of: `rose` (decide first), `amber` (important), `green` (validated), `muted` (can wait)
  - `recommendation` — `{ title, bullets[] }` — what you recommend
  - `alternative` — `{ title, bullets[] }` — the serious alternative (or `alternatives` plural with multiple labelled bullets if 3+)
  - `tradeoff` — short paragraph: what you lose by picking the recommendation
- **Slug** — kebab-case identifier for the output folder. Derive from topic if not given (e.g. `stack-decisions`, `mvp-scope-decisions`).
- **Recipient** (optional) — shapes hero copy.

Use **AskUserQuestion** only if the decisions array is missing critical info. Prefer extracting from conversation context.

If the topic has natural phases (some decisions block others), include an "Order of resolution" section at the top with 3 phase cards. If not, skip it.

## Step 2 — Generate HTML

Generate the full single-file HTML from scratch. Required structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>[Topic] — Decisions</title>
  <!-- Inline all CSS — no external deps except Google Fonts -->
  <style>
    /* parchment palette + Inter + JetBrains Mono */
    :root {
      --bg: #F5F1EB; --surface: #FDFAF6; --accent: #CC785C;
      --green: #4A7C59; --amber: #B8860B; --rose: #B85C5C; --muted: #888;
      --text: #1A1A1A; --text-2: #555;
    }
    /* ... full styles ... */
  </style>
</head>
<body>
  <!-- nav: logo + tag -->
  <!-- hero: eyebrow, h1 with <span class="accent-highlight"> on key word, lead, anchor links -->
  <!-- optional #order section: 3 phase cards (classes a/b/c for rose/amber/green strip) -->

  <!-- #decisions section: one .detail-card per decision -->
  <!--
    Required card structure:
    <div class="detail-card">
      <div class="detail-head">
        <span class="detail-num">#N · PHASE X</span>     <!-- JS reads .detail-num for id -->
        <span class="status-chip status-rose">label</span>
        <span class="detail-title">Decision title</span>  <!-- JS reads .detail-title -->
      </div>
      <div class="detail-body">
        <div class="detail-grid">
          <div>
            <div class="subhead green">Recommendation</div>  <!-- JS detects this label -->
            <div style="font-weight:700">Option title</div>
            <ul class="bullets green">...</ul>
          </div>
          <div>
            <div class="subhead amber">Alternative</div>     <!-- or "Alternatives" -->
            <div>Option title</div>
            <ul class="bullets amber">...</ul>
          </div>
        </div>
        <div class="tradeoff-box">
          <strong>Tradeoff</strong>
          Short paragraph...
        </div>
        <!-- JS auto-injects "✎ Other choice" textarea — do NOT add manually -->
      </div>
    </div>
  -->

  <!-- #summary section -->
  <div id="summaryPanel">...</div>
  <div class="summary-actions">
    <button id="copyBtn">Copy summary</button>
    <button id="resetBtn">Reset</button>
  </div>

  <!-- sticky .decide-bar at bottom with progress + barCopyBtn -->

  <script>
    const STORAGE_KEY = '<slug>-decisions-v1'; // unique per page — prevents localStorage collision
    // ... JS engine ...
    // buildSummary() — update the order array to match your decision IDs:
    // const order = ['1','2','3',...] // IDs in the order you want them in the summary output
    // Update the summary header lines to match your topic
  </script>
</body>
</html>
```

**JS engine requirements:**
- Option detection: reads `.subhead` text, matches `/recommend/i` and `/alternat/i` for auto-highlighting
- Clicking an option toggles `.selected` on that column, persists to localStorage
- `buildSummary()` iterates cards in `order` array, outputs selected option + any "other choice" text
- `copyBtn` / `barCopyBtn` copy summary to clipboard
- `resetBtn` clears localStorage and reloads
- **IDs that must exist:** `summaryPanel`, `doneCount`, `copyBtn`, `barCopyBtn`, `resetBtn`

Save to `/tmp/decisions/<slug>/index.html`.

## Step 3 — Open locally

```bash
mkdir -p /tmp/decisions/<slug>
# (file already written by Write tool)
open /tmp/decisions/<slug>/index.html
```

## Step 4 — Report to user

Reply with:
1. The **local path** (`/tmp/decisions/<slug>/index.html`)
2. How many decisions are on the page
3. One-line update command for future edits: re-run the skill or edit the file directly

Keep under 6 lines.

## Rules

- **Never skip noindex** — these are private decision pages.
- **Don't invent new CSS tokens** — reuse the parchment palette variables.
- **Keep the JS engine intact** — option-detection logic depends on `.subhead` text matching `/recommend/i` and `/alternat/i`.
- **STORAGE_KEY must be unique** per page or pages will share decisions across tabs.
- **Tradeoff is mandatory** for each decision — if you can't articulate a tradeoff, the decision isn't worth a card.
- **"Other choice" is auto-injected by JS** — don't add it in HTML.
