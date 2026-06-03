---
name: one-pager
description: Create a visual one-page HTML page (pitch, status report, roadmap, explainer, reflexão, manifesto, newsletter) and optionally deploy it to your own host with a public URL. Follows the one-pager blueprint — seven style variants (editorial warm, status/tech dark, claude parchment-literary, sonnet parchment-operational, newsprint jornal, swiss minimalist, elevenlabs whisper), 13 transversal visual patterns (eyebrows, flow arrows, feature health grid, status chips, details, tree ASCII, mockups). Use when the user says /one-pager, "faz uma one-pager", "cria uma página para mandar a X", "faz pitch page sobre Y", "cria status page", "faz uma página visual sobre", or asks for a shareable web page that exposes an idea, strategy, proposal, project status, roadmap, reflection, manifesto or newsletter visually.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TaskCreate, TaskUpdate
argument-hint: [tópico] [--style=editorial|status|claude|sonnet|newsprint|swiss|elevenlabs] [--motion] [--to=destinatário] [--slug=custom-slug]
---

# One-Pager — Visual page generator + deployer

Generates a single-file HTML page with diagrams, icons, and structured sections, and optionally deploys it to your own host, returning a shareable public URL.

## The blueprint

The local templates in `templates/` are the canonical reference for the styles and patterns described below. Read the relevant template first to pick up the design tokens and component classes. The skill defines:

- Two style variants (editorial warm · status/tech dark)
- 13 transversal visual patterns (eyebrows, stat cards, flow arrows, feature health grid, status chips, details, tree ASCII, mockup HTML, ref cards, projection table, steps, LIVE STATUS header, mono code)
- Canonical section structure
- An optional, generic deploy flow (nginx + certbot on any host)

## Templates available locally

- `templates/sonnet.html` — Claude palette · operational (parchment `#F5F1EB`, burnt orange `#CC785C`, **100% Inter + JetBrains Mono, sem serif**). Status chips com 4 cores (rose/amber/green/muted), project grid com % de progresso, pipeline flow com setas, action items em duas colunas, steps numerados para next actions. Use for **pitches, propostas, explainers estratégicos, status reports, briefings executivos para cliente, roadmaps**. **Default style.**
- `templates/editorial.html` — Editorial warm pitch (warm cream `#FAFAF6`, teal `#1A9A8B`, Fraunces + Outfit). Use for **pitches externos, explainers com tom editorial/literário** — quando se quer um look distinto.
- `templates/status.html` — Sprint Status (dark ink `#070B18`, cyan `#22D3EE`, Inter + JetBrains Mono, Tailwind CDN, grain texture). Use for **status reports tech dark**, audiências técnicas.
- `templates/claude.html` — Anthropic style (parchment `#F5F1EB`, burnt orange `#CC785C`, Instrument Serif + Inter, literary mood, drop cap, romans minúsculos). Use for **reflexões longas, manifestos, essays, voz pessoal**.
- `templates/newsprint.html` — FT / Economist (papel `#FBF5E8`, ink red `#8B1A1A`, Playfair Display 900 + Source Serif 4, masthead + dateline + columns + pullquote). Use for **newsletter interna, announcements, briefings mensais, updates jornalísticos**.
- `templates/swiss.html` — Dieter Rams / Apple (branco puro, preto puro, Inter 900, grid 12 colunas visível, tipografia 10rem, numeração "01 / Tese"). Use for **manifestos, anúncios dramáticos, pitches uma-ideia-só**.
- `templates/elevenlabs.html` — Premium whisper (white + warm stone `rgba(245,242,239,0.8)`, Manrope 200 + Inter letter-spacing positivo, multi-layer shadows sub-0.1, pill buttons warm). Use for **propostas premium, product landings showcase, bio pages, calma premium**.
- `templates/visual-diagram.html` — **Reference for visual diagram patterns** (cream warm palette, Ubuntu, mobile-first 720px). Not a standalone style — it's a **catalogue of patterns** (icon tiles, funnel rows ✕/✓, filter tables, step connectors, flow nodes, risk/solution pairs, "who" tags, pulse dots, etc.) to layer on top of any base style when the reader is visual or will skim on mobile. See **Visual diagram patterns** section below.

Use these as starting scaffolds. Replace content, keep structure and CSS tokens.

**Tip:** open each template locally in a browser to preview the six styles before picking one.

## Visual diagram patterns (orthogonal)

Reusable patterns for **scannable, mobile-first, diagram-heavy** one-pagers — when the reader is visual, will skim on a phone, and prose-heavy sections won't land. Orthogonal to style choice: layer these on top of any base template.

**Canonical reference:** `templates/visual-diagram.html` (read it to see the patterns in context).

**When to lean visual-heavy:**
- Reader is busy / will skim on mobile
- Reader is visual (designer, marketer, creative)
- Content has structure that diagrams expose better than prose (funnels, flows, pairs)
- Translating a long conversation into something digestible

**When NOT to:** reflexões, manifestos, essays, newsletter — prose carries those.

### Pattern catalogue — pick only what fits the content

Each pattern has a **trigger** (when content fits) and a **anti-trigger** (when it doesn't). Don't force them.

| Pattern | Use when | Don't use when |
|---|---|---|
| **Icon tile** (Lucide SVG in coloured badge + heading + 1-2 sentences) | Any block where an icon adds meaning at a glance | Decoration only — empty icons are noise |
| **Funnel rows** (✕/✓ verdict column + content) | Comparing 3 options where one is the "sweet spot" (segments, tiers, choices) | Linear sequence — use steps instead |
| **Filter table** (check icon + label + verdict pill) | Qualification rules, decision matrix, eligibility criteria | Conceptual lists without yes/no logic |
| **Step list with vertical connector** (numbered circles, dashed line between) | Sequential process / pipeline / journey | Parallel options — use duo grid |
| **Flow nodes + ↓ arrows** (node cards stacked, arrow icons between) | Mechanism or system flow with 3-5 stages | More than 6 stages (becomes wall) |
| **Risk/solution pairs** (red row + gold row, paired) | Honest disclosure of risks with mitigations | Generic "pros/cons" — too neutral |
| **Big stat callout** (large number + label, gold band) | One number deserves attention (timeline, target, metric) | Multiple numbers — use stat grid instead |
| **Pulse dot for "NOW"** (glowing dot + label on the active phase) | Timeline/roadmap with a current phase | No temporal element |
| **"Who" tag pills** (small pills on action items: "Pinhas" / "James" / "Os 2") | Co-owned plan with clear divided responsibility | Solo work, audience reading — pure ruído |
| **Quote card dark** (dark bg, gold accent mark, large body) | One quote / thesis carries the section | Long arguments — use prose tile |
| **Blueprint grid** (small cards with icon + name + 1-line desc, 2-3 cols) | Catalogue of items (products, services, modules) | Fewer than 4 items — use tiles |
| **Phase cards** (timeline with arrow-bullet lists, "NOW" pulse) | A → B strategy with discrete phases | Continuous evolution — use prose |
| **Checklist dark** (numbered checks with optional ownership tag) | Concrete next actions to commit to | Open-ended reflection |

### Visual mechanics — copy from `visual-diagram.html`

- **Lucide-style SVG icons inline** (stroke 2, 22×22 inside 44×44 rounded badge with `var(--accent-soft)` bg). Common icons used: zap, users, shield-check, star, calendar, target, arrow-up-down, send, phone, check, x, alert-triangle, clock, mail, video, file-text, database, settings, message-square. Keep an inventory in the template — copy and recolour as needed.
- **Semantic colour roles** beyond accent: `--green: #4F9D5C` (yes/good), `--red: #C85A3A` (no/risk). Use sparingly — only for verdict states.
- **Mobile-first widths**: `max-width: 720px` (not 880px). Larger feels desktop-heavy.
- **Font size**: 16px body, never below 13px for secondary text.
- **Line height**: 1.45-1.5 for tiles (not 1.6+ — too airy on mobile).
- **Section padding**: 56px y (not 72px) — denser, scrolls faster on phone.
- **Border-radius**: 12-14px on tiles, 999px on pills — consistent rhythm.
- **Tap targets**: anything interactive ≥ 36px tall (we used 44px badge ↔ also touch-safe).

### How to apply

1. Pick base style (`sonnet`, `editorial`, etc.) — it sets palette + fonts.
2. Read `visual-diagram.html` and copy **only** the pattern CSS blocks you need (each pattern is a self-contained CSS group: `.tile`, `.funnel`, `.filter`, `.steps`, `.flow`, `.risks`, `.checklist`, etc.).
3. Adapt the semantic colours (`--green` / `--red`) to play nice with the base palette.
4. **Stay disciplined**: 4-6 patterns max per page. More = noise. Only go higher when the page genuinely has 8+ distinct sections — most one-pagers don't.

## Motion layer (`--motion`)

Orthogonal to the style choice — motion applies on top of any base template. When the user passes `--motion` (or asks for "microanimações", "animado", "premium feel", "motion version"), inject the motion layer from `templates/_motion-layer.html` into the generated page.

What the motion layer adds:

- Scroll progress bar with animated gradient shimmer (top of viewport)
- Cursor spotlight follower (desktop only, `mix-blend-mode: multiply`)
- Reveal-on-scroll with IntersectionObserver + staggered delays
- Hero H1 line-by-line rise reveal (wrap each line in `<span class="line">`)
- Highlight sweep on accent spans inside hero (`.accent-highlight`)
- 3D tilt (perspective 900px, ±6°) on `.feat-card` and `.stat-card`
- Radial spotlight on cards with `data-spot` attribute (cursor-tracked)
- Magnetic pull on buttons with `data-magnet` (25% delta)
- Animated number counters (`data-count`, `data-prefix`, `data-suffix`, easeOutQuart over 1400ms)
- Optional marquee band (`.marquee-band` > `.marquee-track` > `.marquee-item`)
- Animated pipeline arrows (continuous shift)
- Ring pulse on status dots, shimmer lines on dividers, conic gradient spins
- Bullet hover ripple (scale + glow on `.bullets li::before`)
- `prefers-reduced-motion` fallback (disables all animations)

Zero dependencies — all vanilla JS + modern CSS (`@property`, `IntersectionObserver`, `radial-gradient` with CSS custom properties).

**How to inject:**
1. Read `_motion-layer.html` — it contains numbered blocks with instructions in comments
2. Copy `MOTION_TOKENS_CSS` into the base template's `<style>` (at `:root`)
3. Copy `MOTION_UTILITIES_CSS` into the `<style>` block
4. Inject `MOTION_GLOBALS_HTML` (scroll bar + cursor spot divs) right after opening `<body>`
5. Split hero H1 into `<span class="line">` per visual line
6. Add `reveal` class to section-heads, `reveal-stagger` to grid containers
7. Add `data-spot` to cards, `data-magnet` to hero CTAs
8. Convert stat numbers to use `data-count` / `data-prefix` / `data-suffix`
9. Optionally add a `.marquee-band` between hero and first section
10. Inject `MOTION_SCRIPT` right before `</body>`

**When NOT to use `--motion`:**
- `swiss` template (dramatic austerity is the point — motion breaks the mood)
- `newsprint` template (newspaper aesthetic is static by nature)
- Very short one-pagers (<3 sections) — motion needs content to reveal

## Step 1 — Gather inputs

Required:
- **Tópico** — what the page is about. If the user didn't pass it, infer from conversation context or ask.
- **Destinatário** — who reads it (sócio, cliente, parceiro, own reference). Shapes tone.
- **Variante** — `editorial` (default, warm) or `status` (dark, tech). Default to editorial unless the content is clearly a status report / roadmap / sprint update.
- **Motion** — if the user passes `--motion` (or says "com microanimações", "animado", "premium feel", "motion version", "nível tight"), inject the motion layer. Default off.
- **Slug** — URL-safe name for the subdomain (e.g. `wikibicho-pitch`, `menyu-roadmap`). Derive from tópico if not given; kebab-case, ASCII only, short. If motion is on and no slug given, append `-motion` suffix by convention.
- **Pontos-chave** — 3-6 key messages. Extract from conversation if the one-pager is a continuation of an ongoing discussion; otherwise ask.

Use **AskUserQuestion** only if critical info is missing. Prefer inferring from conversation.

## Step 2 — Check slug doesn't collide (only if deploying)

If you plan to deploy to a remote host (optional, see Step 4), check the slug isn't already in use on the server's web root, e.g.:

```bash
ssh <your-server> "ls /srv/www/ | grep ^<slug>$ || echo FREE"
```

If the slug exists, ask the user: overwrite (update existing one-pager) or pick a different slug.

## Step 3 — Generate HTML

Read the appropriate template:

Read the chosen template from the skill's `templates/` directory (e.g. `templates/editorial.html` or `templates/status.html`).

Create a new file at `/tmp/one-pagers/<slug>/index.html` by adapting the template:

1. **Replace all content** — title, hero, sections, footer — with content specific to the tópico.
2. **Keep the CSS tokens and component classes intact.** Don't invent a new design system; reuse the one in the template.
3. **Apply the visual patterns from the blueprint** wherever they fit:
   - Use **flow horizontal with `→`** for any sequence/pipeline/journey
   - Use **feature health grid with %** if there's progress/status data
   - Use **status chips** (Feito / Por fazer / Contínuo) for any action items
   - Use **`<details>` colapsáveis** if any section has >5 items of dense content
   - Use **tree ASCII** for architecture / URL structure / folder hierarchy
   - Use **mockup HTML** if explaining a user-facing interface
   - Use **ref cards grid** for external references / inspirations
   - Use **LIVE STATUS** header with pulsing dot for "this is current state" feel
   - Use **mono font** for commits, paths, IDs, flags, variables
4. **Sections follow the canonical structure** (eyebrows numbered 01, 02...) but only include what's relevant. A short explainer might have 4 sections; a full pitch might have 9.
5. **Update metadata**: `<title>`, `<meta description>`, `<meta robots="noindex,nofollow">` is mandatory.
6. **Footer** should say "preparado por [a tua empresa / o teu nome] · [ano]" — ask the user how they want to be credited if it's not obvious from context.
7. **If `--motion` flag is on:** read `templates/_motion-layer.html` and inject its blocks per the comments there. Checklist:
   - `MOTION_TOKENS_CSS` added to `:root` (match `--accent-glow` to the template's accent rgba)
   - `MOTION_UTILITIES_CSS` added to main `<style>`
   - `<div class="scroll-progress">` + `<div class="cursor-spot">` right after `<body>`
   - Hero H1 split into `<span class="line">` per line; accent word wrapped in `<span class="accent-highlight">`
   - `reveal` class on each `.section-head`; `reveal-stagger` on each grid container (`.stats-grid`, `.problem-grid`, `.features-grid`, `.workflow-stack`, `.biz-grid`, `.steps`)
   - `data-spot` on cards that should get radial spotlight (`.feat-card`, `.stat-card`, `.prob-card`, `.biz-card`)
   - `data-magnet` on hero CTA buttons (`.mark`)
   - Stat numbers: convert to `data-count="300" data-prefix="~" data-suffix="%"` with initial text `~0%`
   - Optional: add `.marquee-band` between hero and first section with 6-8 duplicated `.marquee-item` facts
   - `MOTION_SCRIPT` injected right before `</body>`

Save to `/tmp/one-pagers/<slug>/index.html`. Keep the temp copy around so the user can edit afterwards with simple `scp` re-deploy.

## Step 4 — Deploy (optional)

The output is a single self-contained `index.html`. The simplest "deploy" is to just open it locally or send the file. If the user wants a public URL, deploy it to **their own host** — the skill is not tied to any particular provider.

The block below is a **generic reference** for serving the page behind nginx + Let's Encrypt on a Linux server. Replace the placeholders (`<your-server>`, `<your-domain>`, `you@example.com`, web root) with the user's own values. Run the steps in sequence; if any fails, stop and report the error.

```bash
# Placeholders to fill in:
#   <your-server>  — ssh host alias or user@ip of your server
#   <your-domain>  — the (sub)domain to serve, e.g. <slug>.example.com
#   you@example.com — email for the Let's Encrypt account
#   WEBROOT        — where static sites live on your server, e.g. /srv/www

# Create dir + upload
ssh <your-server> "mkdir -p WEBROOT/<slug> && chown -R www-data:www-data WEBROOT/<slug>"
scp /tmp/one-pagers/<slug>/index.html <your-server>:WEBROOT/<slug>/index.html

# Nginx config (skip if slug exists and we're just updating)
ssh <your-server> "cat > /etc/nginx/sites-available/<slug> << 'NGINX_EOF'
server {
    listen 80;
    listen [::]:80;
    server_name <your-domain>;

    location /.well-known/acme-challenge/ {
        root /srv/acme;
    }

    location / {
        root WEBROOT/<slug>;
        index index.html;
        try_files \$uri \$uri/ =404;

        add_header X-Content-Type-Options \"nosniff\" always;
        add_header X-Frame-Options \"SAMEORIGIN\" always;
        add_header Referrer-Policy \"no-referrer-when-downgrade\" always;
        add_header X-Robots-Tag \"noindex, nofollow\" always;
    }

    access_log /var/log/nginx/<slug>.access.log;
    error_log /var/log/nginx/<slug>.error.log;
}
NGINX_EOF
ln -sf /etc/nginx/sites-available/<slug> /etc/nginx/sites-enabled/<slug>
nginx -t && systemctl reload nginx"

# SSL (skip if cert already exists for this domain)
ssh <your-server> "certbot --nginx -d <your-domain> \
  --non-interactive --agree-tos -m you@example.com --redirect"

# Verify
curl -sI https://<your-domain> | head -3
```

**Skipping on update:** if the slug already exists in the web root, skip the nginx config + certbot steps — just `scp` the new HTML.

## Step 5 — Keep an index (optional)

If you maintain a log of generated one-pagers (e.g. a notes file), append a row for the new page:

`| 2026-MM-DD | <título> | <variante> | <url-or-path> | <contexto curto> |`

## Step 6 — Report to the user

Reply with:

1. The **URL** if deployed (prominently, on its own line, ready to copy) — otherwise the local file path.
2. The **local path** (`/tmp/one-pagers/<slug>/index.html`) for future edits.
3. **One-line next steps**: how to update (re-`scp` the new HTML if deployed) and how to delete.

Keep the report under 10 lines.

## Rules

- **Variante default is editorial** unless the content is clearly a status/roadmap/sprint update.
- **Never skip noindex** — these are private one-pagers, never public product pages.
- **Footer autor** should match how the user wants to be credited (their company or personal name). Ask if unclear.
- **Don't invent new CSS tokens** — reuse the templates' design systems.
- **Mobile check** is implicit — the templates already handle responsive grids. Don't break them.
