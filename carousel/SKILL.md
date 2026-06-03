---
name: carousel
description: Gera carrosseis Instagram (1080×1350 PNG) para marcas no sistema ~/Brands/. Pipeline em 3 agentes: Planner (plan.json) → Executor (index.html + render.py) → Reviewer (review.json com pass/fail). Reviewer loop até pass (máx 3). Usar quando o utilizador pedir /carousel, "faz um carrossel", "cria slides para", "carrossel da Acme sobre X", ou qualquer geração de slides Instagram para uma marca.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: <brand> [tema] [--slides=N] [--slug=custom-slug]
---

# Carousel — Gerador de carrosseis Instagram

Pipeline: **Transcript (se episódio) → Planner → Executor → Renderer → Reviewer (loop)**

### Convenção de pastas (`~/Brands/`)

Cada marca vive numa pasta `~/Brands/<brand>/` com:
- `brand.json` — tokens de cor, tipografia, handle, hashtags, defaults de carrossel
- `BRAND.md` — voz, spelling variant, notas editoriais
- `assets/logos/` — ficheiros de logo
- `output/<slug>/v1/` — onde o skill escreve plan.json, index.html, render.py, slides/

Esta convenção é genérica — adapta `<brand>` ao nome da pasta da tua marca.

---

## ⚠️ REGRA OBRIGATÓRIA — Carrosseis de episódios

Quando o tema é um episódio de podcast/vídeo (qualquer série editorial), o conteúdo **NUNCA pode ser inventado**. Slides com quotes/statements têm de basear-se no **transcrito real**.

**Workflow para episódio:**
1. **Antes do Planner**, extrair transcrito:
   ```bash
   yt-dlp --skip-download --write-auto-sub --sub-lang "pt,pt-PT" --convert-subs srt \
     --output "{{slug}}.%(ext)s" "{{youtube_url}}"
   # Converter VTT/SRT para texto plano
   awk '!/^[0-9]+$/ && !/-->/ && NF' file.srt | sed 's/<[^>]*>//g' > transcript.txt
   ```
2. **Ler transcrito por inteiro** antes de gerar `plan.json`. Identificar passagens-chave do convidado/host.
3. **No `plan.json`**, cada slide com texto editorial deve ter campo `source`:
   - `"verbatim"` — citação directa (com aspas + atribuição)
   - `"summary"` — resumo/paráfrase próxima de algo dito (sem aspas, apresentado como statement)
   - `"editorial-meta"` — título, créditos, plataformas (OK para capa, slide convidado, CTA)
   - `"historical"` — citação histórica documentada (ex: frase real do Mikao Usui)
4. **Citações** sempre com aspas `«…»` + atribuição visível. Sem atribuição = não é citação.
5. **Reviewer deve validar:** existe transcrito, citações têm match no transcrito (grep), resumos têm correspondência.

**Excepções:** carrosseis editoriais que NÃO promovem episódio (reflexões, anúncios, valores) ficam livres deste constraint.

---

## Passo 1 — Inputs

Argumentos obrigatórios:
- **brand** — nome da pasta em `~/Brands/` (ex: `acme`)
- **tema** — assunto do carrossel (episódio, artigo, tema editorial)
- **fonte** — URL, texto colado, ou brief escrito pelo utilizador

Argumentos opcionais (perguntar só se não óbvio do contexto):
- **n_slides** — número de slides (default: 7; mín: 3; máx: 10)
- **slug** — nome do output dir (default: kebab-case do tema)

Usar `AskUserQuestion` apenas se `brand` ou `tema` estiverem ausentes e não forem inferíveis da conversa.

---

## Passo 2 — Ler brand files

```bash
cat ~/Brands/<brand>/brand.json
cat ~/Brands/<brand>/BRAND.md
```

Extrair e guardar mentalmente:
- `handle` (Instagram) — vai no chrome-top e chrome-bottom de todos os slides
- `short_name` — vai no chrome-bottom dos slides sem dots
- Logo path: `~/Brands/<brand>/assets/logos/<primary_logo>` — usar path absoluto no HTML
- Paleta de tokens (cream, dark, gold, ink, muted)
- Tipografia (família serif e sans)
- Voz e spelling variant (ex: pré-AO90)

---

## Passo 3 — PLANNER: gerar plan.json

Criar `~/Brands/<brand>/output/<slug>/v1/plan.json`.

### Estrutura do plan.json

```json
{
  "brand": "<brand>",
  "slug": "<slug>",
  "format": "1080x1350",
  "source": { "desc": "breve descrição da fonte" },
  "design_direction": {
    "mood": "editorial-minimalist",
    "rules": [
      "Chrome zones (top 100px / bottom 100px) reservadas — conteúdo nunca invade",
      "Logo/selo só na capa (slide 1) e CTA (slide final)",
      "Alternância cream/dark para pacing",
      "Headlines em Cormorant Garamond (italic=emoção, roman=argumento)",
      "Body em Outfit Light 300/400",
      "Whitespace é o efeito visual — nunca preencher só por preencher",
      "Zero ornamentos: sem traços soltos, sem círculos numerados",
      "Paginação: dots no rodapé, posição idêntica em todos os slides"
    ]
  },
  "tokens": {
    "cream": "#EDE5D4",
    "cream_dim": "#D9CFB8",
    "dark": "#0E0C0A",
    "ink_on_cream": "#1A1612",
    "ink_on_dark": "#EDE5D4",
    "muted_on_cream": "#6B5E4D",
    "muted_on_dark": "#8A8070",
    "gold": "#C9A84C"
  },
  "narrative_arc": "<1 parágrafo descrevendo o storytelling dos slides>",
  "slides": [ ... ]
}
```

### Slide roles e layouts

| Role | Layout | Variantes opt-in | BG default | Campos obrigatórios |
|------|--------|------------------|------------|---------------------|
| capa | L1 | `.has-image` (full-bleed image + scrim + eyebrow badge) | cream | eyebrow, title_italic, title_roman, subtitle (opcional) |
| hook_quote / citação | L2 | — | dark | quote (pode ter .ro + .it), attribution (opcional) |
| tensão / reposicionamento | L2, L3 ou L6 | L6 com imagem/símbolo | dark/cream | L2: quote±attribution; L3: headline+body; L6: image + headline + body |
| origem / desenvolvimento | L3 ou L6 | L6 com imagem | cream | headline_italic + headline_roman + body |
| convidado | L4 | `.with-image` (portrait top 50% + texto bottom) | cream | label, name, credentials (lista) |
| cta | L5 | `.platform` icons SVG (YT, Spotify, Apple, etc.) | dark | cta_headline, cta_sub, platforms, bio_cta, handle |

**Variantes específicas (opt-in por marca):**
- **L1.has-image** — usar quando capa precisa de impacto visual (face do convidado, atmosfera do episódio). Imagem em full-bleed com scrim gradient (heavy bottom para legibilidade do título) + eyebrow em badge frosted dark chip pill.
- **L4.with-image** — usar quando há retrato profissional do convidado (não foto de bastidores).
- **L6** — usar para tensão/origem com suporte visual. Imagem ocupa 60% topo, texto cream 40% baixo. Variante `.symbol-blend` para kanji/símbolos com `background-blend-mode: multiply`.

Per-brand defaults vêm de `~/Brands/<brand>/brand.json` campo `carousel.approved_design_*`. **Não assumir que estes layouts são default para todas as marcas** — só usar quando o `brand.json` declara o variant aprovado.

### Regras do Planner

⚠️ **Tamanhos mínimos para legibilidade mobile (regra crítica, calibrada Maio 2026):**
No Instagram mobile, os slides 1080×1350 são renderizados a ~400px de largura (rácio ~2.7×). Tudo abaixo de **22px source** torna-se ilegível. Mínimos:

- **chrome-top:** 24px · **chrome-bottom:** 20px · **chrome-bottom .org:** 18px · **dots:** 9×9px
- **eyebrow / labels / attributions:** ≥ 22px (com letter-spacing alto, contar com mais espaço)
- **body text (L6):** ≥ 30px
- **subtitle (L1):** ≥ 32px
- **CTA sub / bio / handle:** ≥ 26px

Headlines (60-156px) e quotes (≥64px) já estão acima do limite — manter como estão. Só os pequenos precisam destes mínimos.

1. **Narrative arc obrigatório** — Hook → Tensão → Reposicionamento → [Origem/Convidado] → CTA. Escrever 1 parágrafo que descreve o storytelling.
2. **Italic vs roman** — italic = emoção/citação/nome; roman = argumento/conclusão. Cada headline pode misturar: primeira parte italic (entrada), segunda parte roman (peso).
3. **Alternância dark/cream** — nunca 3 slides seguidos da mesma cor.
4. **Slide 1 sempre cream**, **slide final (CTA) sempre dark**.
5. **show_logo=true** apenas nos slides com role capa e cta. Todos os outros: show_logo=false.
6. **Capa (slide 1) sem page indicator**. Todos os outros com page indicator (dots).
7. **Voz do brand** — usar spelling variant do brand.json (ex: pré-AO90: "acção", não "ação").
8. **Conteúdo por slide**: uma ideia. Máx 2 frases no body. Whitespace é o efeito visual.

---

## Passo 4 — EXECUTOR: gerar index.html + render.py

### 4.1 Criar directório de output

```bash
mkdir -p ~/Brands/<brand>/output/<slug>/v1/slides
```

### 4.2 Determinar logo path

O logo vai no HTML como caminho relativo ou absoluto. Verificar:
```bash
ls ~/Brands/<brand>/assets/logos/
```
Usar o path do logo no CSS (`.l1 .seal` e `.l5 .seal`) como:
- URL relativa se render.py estiver na mesma pasta: `url('../../assets/logos/<logo-file>')`
- Ou path absoluto: `url('$HOME/Brands/<brand>/assets/logos/<logo-file>')` (expandir `$HOME` para o caminho real ao escrever o HTML)
**Preferir path absoluto** — mais robusto com Playwright file://.

### 4.3 Gerar index.html

Usar `templates/base.html` (na pasta deste skill) como scaffold CSS.

Estrutura de cada slide:

```html
<section id="slide-N" class="slide <bg> <layout>">
  <div class="chrome-top">
    <span class="handle">@<instagram_handle></span>
    <span class="badge"><série> · #<número></span>
  </div>
  <div class="content">
    <!-- conteúdo do layout -->
  </div>
  <div class="chrome-bottom">
    <!-- slide 1 (capa): apenas <span class="org"><short_name></span> sem dots -->
    <!-- restantes slides: dots + org -->
    <div class="pages">
      <!-- N dots, um por slide, .active no slide actual -->
      <span class="dot"></span> × (N-1)
      <span class="dot active"></span> ← slide actual
    </div>
    <span class="org"><short_name></span>
  </div>
</section>
```

**Conteúdo por layout:**

**L1 — capa:**
```html
<div class="seal"></div>  <!-- logo: absolute, top 130px left 80px -->
<p class="eyebrow">EYEBROW</p>
<h1 class="title">
  <span class="it">TÍTULO_ITALIC</span>
  <span class="ro">TÍTULO_ROMAN</span>
</h1>
<p class="subtitle">SUBTITLE</p>  <!-- omitir se ausente -->
```

**L2 — quote:**
```html
<p class="quote">
  <!-- Se apenas italic: texto directo -->
  <!-- Se roman+italic misturado: -->
  <span class="ro">PARTE_ROMAN</span><br>
  <span class="it">PARTE_ITALIC</span>
</p>
<p class="attribution">ATRIBUIÇÃO · DATA</p>  <!-- omitir se attribution=null -->
```

**L3 — statement:**
```html
<h2 class="headline">
  <span class="it">HEADLINE_ITALIC</span>
  <span class="ro">HEADLINE_ROMAN</span>
</h2>
<p class="body">BODY_TEXT</p>
```

**L4 — guest:**
```html
<p class="label">EYEBROW</p>
<h2 class="name">NOME_CONVIDADO</h2>
<ul class="creds">
  <li>CREDENCIAL_1</li>
  <li>CREDENCIAL_2</li>
</ul>
```

**L5 — cta (com ícones oficiais SVG):**
```html
<div class="seal"></div>
<p class="cta-headline">EPISODE_OFFICIAL_TITLE</p>
<p class="cta-sub">com CONVIDADO · parte N · NOME_DA_SÉRIE #N</p>
<div class="platforms">
  <div class="platform youtube">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-label="YouTube">
      <path fill="#FF0000" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814z"/>
      <path fill="#FFFFFF" d="M9.546 15.568V8.432L15.818 12l-6.272 3.568z"/>
    </svg>
    <span class="platform-label">YouTube</span>
  </div>
  <div class="platform spotify">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-label="Spotify">
      <circle cx="12" cy="12" r="12" fill="#0E0C0A"/>
      <path fill="#1DB954" d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12C24 5.4 18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>
    </svg>
    <span class="platform-label">Spotify</span>
  </div>
</div>
<p class="bio-cta">O link encontra-se no nosso <span class="gold">perfil</span>.</p>
<p class="handle">@HANDLE</p>
```

Notas sobre os SVGs:
- **YouTube**: dois paths — rectângulo vermelho `#FF0000` (perímetro completo, sem cut-out) + triângulo branco `#FFFFFF` por cima. **Não usar versão com cut-out** (o play ficaria transparente e mostraria fundo do slide). Fundo do SVG é transparente — não há halo branco.
- **Spotify**: círculo `#0E0C0A` (preto profundo) por trás + path verde `#1DB954` com cut-outs nas ondas. Ondas mostram o preto através. **Cores oficiais.** Nunca usar branco para as ondas.

**L1 — capa com imagem full-bleed (variante `.has-image`):**
```html
<section id="slide-1" class="slide l1 has-image">
  <div class="bg-image"></div>  <!-- background: url('IMAGEM_HERO') center/cover -->
  <div class="chrome-top">...</div>
  <div class="content">
    <p class="eyebrow">EYEBROW</p>  <!-- estilo automaticamente badge pill -->
    <h1 class="title">
      <span class="it">TÍTULO_ITALIC</span>
      <span class="ro">TÍTULO_ROMAN</span>
    </h1>
    <p class="subtitle">SUBTITLE</p>
  </div>
  <div class="chrome-bottom">...</div>
</section>
```

**L4 — convidado com retrato (variante `.with-image`):**
```html
<section class="slide cream l4 with-image">
  <div class="chrome-top">...</div>
  <div class="content">
    <div class="portrait"></div>  <!-- background: url('PORTRAIT_PATH') center 25%/cover -->
    <div class="text-area">
      <p class="label">EYEBROW LABEL</p>
      <h2 class="name">NOME_CONVIDADO</h2>
      <ul class="creds">
        <li>CREDENCIAL_1</li>
        <li>CREDENCIAL_2</li>
      </ul>
    </div>
  </div>
  <div class="chrome-bottom">...</div>
</section>
```

**L6 — imagem topo + texto baixo (60/40):**
```html
<section class="slide cream l6">
  <div class="chrome-top">...</div>
  <div class="content">
    <div class="image"></div>  <!-- background-image inline ou class específica -->
    <div class="text-area">
      <h2 class="headline">
        <span class="it">HEADLINE_ITALIC</span>
        <span class="ro">HEADLINE_ROMAN</span>
      </h2>
      <p class="body">CITAÇÃO ou RESUMO baseado no transcrito (com aspas se for verbatim).</p>
    </div>
  </div>
  <div class="chrome-bottom">...</div>
</section>
```
Variante para kanji/símbolos: adicionar classe `.symbol-blend` à `<div class="image">` → usa `background-blend-mode: multiply` para integrar imagem PNG/JPG com fundo branco em cream.

### REGRAS CRÍTICAS DO EXECUTOR

1. **Nunca multiplicar spans** — se plan.json diz `headline_italic` + `headline_roman`, são exactamente 2 spans (.it + .ro). Nunca 3, 4, 5.
2. **Logo path absoluto** — `url('$HOME/Brands/<brand>/assets/logos/<logo>')` (expandir `$HOME`). Nunca inventar path.
3. **Dots page indicator** — gerar N dots para N slides totais; o dot do slide actual tem class `.active`. Slide 1 (capa) não tem dots.
4. **Body text** — copiar do plan.json sem alterar. Respeitar spelling variant.
5. **Badge no chrome-top** — só incluir se o plano indicar série/episódio. Omitir se o carrossel não for de série.

### 4.4 Gerar render.py

Copiar `templates/render.py` (na pasta deste skill) sem alterações.
O render.py lê `plan.json` para saber o número de slides.

⚠️ **Bug histórico — font-load timing (resolvido no template):** se um slide com quote em Cormorant italic renderizar como caixa cinzenta sólida (em vez de texto), a causa é a font-face italic não estar carregada quando o screenshot é tirado. O template actual faz pré-load explícito via `document.fonts.load(...)` para todas as variantes/tamanhos. Não remover esse bloco. Se aparecer um glitch novo num tamanho não coberto, adicionar a linha correspondente.

---

## Passo 5 — RENDER

```bash
cd ~/Brands/<brand>/output/<slug>/v1/
python3 render.py
```

Se falhar:
- `ModuleNotFoundError: playwright` → `pip install playwright && playwright install chromium`
- `ModuleNotFoundError: PIL` → não necessário no render.py canónico; ignorar
- `MISS #slide-N` → slide não existe no HTML; verificar se o Executor gerou todos os slides do plan.json

Verificar dimensões antes de passar ao Reviewer:
```bash
python3 -c "from PIL import Image; [print(f'{p.name}: {Image.open(p).size}') for p in sorted(Path('slides').glob('*.png'))]" 2>/dev/null || \
  ls -lh slides/*.png
```

---

## Passo 6 — REVIEWER: gerar review.json

Ler todos os PNGs de `slides/` e verificar **por slide**:

| Check | Critério | Pass se... |
|-------|----------|------------|
| **overlap** | Texto sobre logo / logo sobre texto / chrome sobre conteúdo | Nenhum elemento visualmente sobreposto |
| **contrast** | WCAG AA mínimo | Texto claramente legível sobre fundo |
| **typo_match** | Familia, peso, italic/roman bate com plan.json | Headline é serif (Cormorant), body é sans (Outfit) |
| **hierarchy** | Headline 5–8× maior que body | Headline claramente dominante |
| **highlight_count** | Máximo 1 ênfase por slide | 0 ou 1 |
| **plan_fidelity** | Texto, layout, bg, italic/roman, dots correcto | Tudo bate com plan.json |
| **chrome_consistency** | Chrome na mesma posição em todos os slides | Alinhamento idêntico |

Output `review.json`:

```json
{
  "pass": false,
  "slides": [
    { "n": 1, "pass": true, "issues": [] },
    { "n": 2, "pass": false, "issues": [
      { "check": "typo_match", "desc": "Quote inteiramente italic — devia ter .ro para 'Não é uma técnica de cura.'" }
    ]}
  ],
  "fixes": [
    "slide-2: adicionar <span class=\"ro\"> à primeira parte da quote"
  ]
}
```

Escrever `review.json` em `~/Brands/<brand>/output/<slug>/v1/review.json`.

---

## Passo 7 — Loop até pass (máx 3)

Se `review.json.pass == false`:
1. Aplicar cada fix de `review.json.fixes` no `index.html`
2. Re-correr `python3 render.py`
3. Re-rever os slides corrigidos
4. Actualizar `review.json`
5. Repetir até pass ou até 3 loops atingidos

Se após 3 loops ainda houver falhas: reportar ao utilizador com lista de issues por resolver — não entregar como pass.

---

## Passo 8 — Captions

Quando `review.json.pass == true`:

1. Gerar **captions IG/FB/LinkedIn** em `~/Brands/<brand>/output/<slug>/v1/captions.md` (com a voz e spelling variant da marca):
   - 1 parágrafo de 2–4 frases (hook do carrossel em texto)
   - Hashtags do `brand.json` (base + by_theme conforme o tema)
   - CTA subtil institucional (variação do template do brand.json)
   - Captions ligeiramente diferentes entre FB e IG (não copy-paste exacto)
2. (Opcional) Registar a geração no teu próprio sistema de tracking/log, se tiveres um.

---

## Passo 9 — Preview HTML + deploy (OPCIONAL)

Este passo é opcional e só interessa se quiseres rever os carrosseis num dashboard web partilhado. A geração dos PNGs nos passos anteriores é o entregável principal — funciona sem nada disto.

### 9.1 Gerar `preview.html`

Criar `~/Brands/<brand>/output/<slug>/v1/preview.html` — grelha visual dos PNGs com zoom on click. Template em `templates/preview.html` (versão simples baseada em PNGs). Ajustar:
- `<title>` com nome do carrossel
- Header com título italic + subtítulo
- N cards `<div class="slide-wrap">` (um por slide), com `data-src` apontando para `slides/slide-NN.png` e legenda curta no `<div class="slide-meta">`
- **Botão "📁 Abrir pasta local"** — ajustar `data-path="$HOME/Brands/<brand>/output/<slug>/v1/slides"` (path absoluto local, expandir `$HOME`). O JS já incluído faz tentativa `file://` + cópia para clipboard com toast.

### 9.2 Deploy a um host (opcional)

Se quiseres servir o `preview.html` + `slides/` num host próprio, faz upload por `rsync`/`scp` para o teu servidor. Exemplo genérico:

```bash
# Substitui <your-server> pelo alias SSH do teu host e <remote-path> pelo destino.
ssh <your-server> "mkdir -p <remote-path>/<slug>"

cd ~/Brands/<brand>/output/<slug>/v1/
rsync -avz \
  --exclude='transcript' \
  --exclude='render.py' \
  --exclude='plan.json' \
  --exclude='review.json' \
  --exclude='captions.md' \
  --exclude='.DS_Store' \
  . <your-server>:<remote-path>/<slug>/
```

Sobem: `index.html` (source HTML), `preview.html`, `logo.png`, `slides/`, `assets/`.

Depois do upload, verifica que o host devolve `200`:

```bash
curl -s -o /dev/null -w "%{http_code}\n" "https://<your-host>/<slug>/preview.html"
curl -s -o /dev/null -w "%{http_code}\n" "https://<your-host>/<slug>/slides/slide-01.png"
```

### 9.3 Reportar

Reportar ao utilizador:
- Caminho dos slides locais
- (Se deployado) URL do preview do novo carrossel
- Captions disponíveis em `captions.md`

---

## Constraints OBRIGATÓRIOS (resumo)

1. **Output ≤ 2000px** — SCALE=1 sempre. Sem excepções.
2. **Chrome zones reservadas** — `grid-template-rows: 100px 1fr 100px`. Nunca.
3. **Logo só na capa e CTA** — todos os outros slides: handle textual.
4. **Italic/roman exactamente como plan.json** — nunca inventar segmentos extra.
5. **Reviewer obrigatório** — nunca entregar sem review.json pass.
6. **Deploy é opcional** — o Passo 9 só corre se o utilizador quiser um preview web.
7. **Fechar Playwright** — o render.py já fecha; não invocar browser externo.
8. **Verificar logo path existe** antes de escrever HTML.
9. **Voz do brand** — spelling variant do brand.json (ex: pré-AO90 se a marca o usar).

---

## Exemplo de invocação

```
/carousel acme "Café de especialidade #21 — Métodos de extração"
```

Ou com brief colado no chat — o Planner usa o conteúdo para gerar a narrativa.
