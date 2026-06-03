---
name: proof
description: Gera provas visuais das alterações feitas numa sessão, para o utilizador validar antes de mostrar ao cliente. Por defeito gera uma página HTML (screenshots à esquerda, painel "PEDIDO DO CLIENTE / O QUE FOI FEITO / O QUE TENS DE APROVAR" à direita, bolinhas numeradas via overlay) — leve e partilhável por link. Modo alternativo "pil"/"--legendado" gera PNGs com a legenda embebida na própria imagem (bolinha + seta). Output em ~/Desktop/<projecto>-proof-<data>/. Use this skill whenever the user types /proof, /provas, "cria proof", "cria provas", "faz prints das alterações", "gera provas para o cliente", "screenshots legendados", or "quero ver o que mudaste" — tipicamente depois de um conjunto de alterações pedidas pelo cliente.
---

# Provas — Página visual das alterações

Skill para gerar provas visuais de um conjunto de alterações. Cada prova mostra um screenshot do elemento alterado e três secções fixas:

1. **PEDIDO DO CLIENTE** — o que foi pedido (idealmente citado)
2. **O QUE FOI FEITO** — implementação (referenciando os números das bolinhas)
3. **O QUE TENS DE APROVAR** — decisão concreta para o utilizador

## Dois modos de output

- **HTML (default)** — uma página `index.html` com os screenshots à esquerda e o painel das 3 secções à direita; bolinhas numeradas como overlay CSS sobre a imagem. É o modo recomendado: gasta **menos** tokens (não há cálculo de coordenadas de seta nem verificação pixel-a-pixel), é mais legível e dá-te **1 link** para validar (e partilhar). Tem ainda um toggle **"Modo cliente"** que esconde o bloco "O QUE TENS DE APROVAR" para mandares ao cliente.
- **PIL (`/proof pil` ou `/proof --legendado`)** — o formato original: cada prova é um PNG com **bolinha numerada + seta** a apontar para o elemento, e a caixa de legenda embebida abaixo. Útil quando precisas de imagens auto-contidas (anexar a um email, colar num chat) sem depender de uma página.

Output (nos dois modos) em `~/Desktop/<projecto-slug>-proof-<YYYY-MM-DD>/`.

## Quando executar

- Utilizador escreveu `/provas` ou variação (ver `description`)
- Sessão actual já fez um conjunto de alterações que precisam ser validadas visualmente antes do utilizador as mostrar ao cliente
- Tipicamente depois de implementar pedidos de feedback de um stakeholder

**Escolha de modo (parâmetro):** se o utilizador passar `pil` ou `--legendado` (ex: `/proof pil`), usar o modo PIL (PNGs com legenda embebida). Caso contrário, usar o modo **HTML** (default).

## Pré-requisitos

- `pdftoppm` (Poppler) — instalado via Homebrew: `brew install poppler`
- `python3` com PIL — `python3 -c "from PIL import Image"` deve passar
- Playwright + Chromium (para capturas de UI)
- App em produção acessível (ou dev server local)
- Credenciais de teste do projecto

## Passos

### 1. Identificar as alterações

Listar o que mudou desde o último ponto de validação:
```bash
# Commits desde o último push ao main (ou últimos N commits)
git log origin/main..HEAD --oneline 2>/dev/null || git log -10 --oneline
```

Combinar com o contexto da conversa actual — o agente já sabe o que implementou nesta sessão. Para cada item, definir:
- **Título curto** (ex: "Sidebar — Ed. 2025")
- **Tipo de captura**: UI (Playwright), PDF (preview-endpoint), HTML (fetch + grep), outro

### 2. Confirmar com o utilizador

Mostrar a lista numerada e perguntar se está completa, se há algo a remover, ou se a ordem está certa. Não avançar sem aprovação implícita.

### 3. Capturar evidência

**Para UI (sidebar, formulários, páginas com login):**
Usar Playwright + login via Supabase Auth. Script template em `~/.claude/skills/proof/capture-ui.mjs` (copiar para `/tmp/<projecto>-proof/` e adaptar).

**Para PDFs (capas, rodapés, layout):**
Usar o endpoint admin (`/api/admin/users/[id]/preview-pdf/[type]`) que regenera o PDF fresco. Login como admin, ir buscar o cookie SSR, fetch para `/tmp/<projecto>-pdf/<fase>.pdf`. Renderizar página com `pdftoppm -r 150 -f N -l N <pdf> <prefix>` (página 1 = capa, página 2+ = miolo/rodapé).

Para rodapés/cropes específicos, usar PIL para cortar:
```python
img = Image.open("...png"); w, h = img.size
crop = img.crop((0, h - 90, w, h)); crop.save("footer-only.png")
```

### 4. Preencher os items

Os dois modos partilham a **mesma estrutura `ITEMS`**, por isso preenche-a uma vez e escolhe o script no passo 5.

- Modo HTML (default): copiar `~/.claude/skills/proof/build-html.py` para `/tmp/<projecto>-proof/build-html.py`.
- Modo PIL: copiar `~/.claude/skills/proof/add-captions.py` para `/tmp/<projecto>-proof/add-captions.py`.

No topo do script editar `SRC`, `DEST` (e, no HTML, `PROJECT_TITLE`/`PROJECT_DATE`) e a lista `ITEMS`:

```python
{
    "src": "ficheiro-fonte.png",                     # ficheiro em /tmp/<projecto>-proof/
    "dst": "01-<descricao>.png",                     # nome base do output
    "num": "1",                                       # número da prova (string)
    "status": "ok",                                   # "ok" (verde) ou "bug" (vermelho)
    "pedido": 'Cliente: "<citação directa>"',
    "feito": '(1) <implementação>. (2) <outra>...',  # números batem com markers
    "approve": "<decisão concreta>.",
    "markers": [
        {"n": 1, "x": 115, "y": 610},                # x,y = ponto a destacar na imagem original
        # PIL usa ainda "side" ("left"|"right"|"above"|"below") + "offset"; o HTML ignora-os.
    ],
},
```

**Markers — HTML (default):**
- A bolinha fica **sobre** o ponto `(x, y)` (overlay em %, convertido lendo as dimensões da imagem). Não precisas de `side`/`offset` nem de verificação pixel-a-pixel — se ficar ligeiramente desalinhada, o painel ao lado explica à mesma.
- `markers` é **opcional**. Sem markers, mostra só o screenshot + painel (mais leve em tokens).

**Markers — PIL:**
- O `(x, y)` aponta para o **elemento a destacar**, não para o badge. A seta sai do badge e termina perto do anchor sem o tocar (gap automático de ~14px).
- A bolinha **nunca pode tapar** o elemento. Escolher `side` para a direcção onde há mais espaço branco.
- Para texto fino (data, label): anchor à borda esquerda do texto + `side="left"` com `offset=75` (badge fica no margin).
- Para campos largos: `side="above"` ou `"below"` resulta melhor que `"left"`.
- Coordenadas são em **pixels da imagem original** (antes de qualquer padding). Para PDFs A4 a 150 DPI: imagem 1240×1754, e PDF coord × 2.083 = pixel coord.

### 5. Gerar

**Modo HTML (default):**
```bash
python3 /tmp/<projecto>-proof/build-html.py
open ~/Desktop/<projecto-slug>-proof-<data>/index.html
```
Copia os screenshots para a pasta de output e escreve `index.html` (referências relativas — funciona local e em deploy). Para partilhar por link, deployar a pasta como site estático (Netlify, GitHub Pages, um VPS, etc.).

**Modo PIL (`/proof pil`):**
```bash
python3 /tmp/<projecto>-proof/add-captions.py
open ~/Desktop/<projecto-slug>-proof-<data>/
```
Desenha markers (badge + seta) nas coords originais, pad imagens estreitas (<900px), renderiza a caixa de legenda e salva cada `<dst>.png`.

### 6. Verificar

- **HTML:** abrir o `index.html` e confirmar que cada prova tem o screenshot certo, o painel legível, e o número da bolinha bate com o `(n)` no texto "O QUE FOI FEITO". Testar o toggle "Modo cliente". Ajustes de posição de bolinha fazem-se no browser, sem re-ler imagens.
- **PIL:** ler cada PNG gerado e confirmar que o badge não tapa o elemento, a seta aponta certo, a legenda é legível, e o número bate. Se um marker estiver mal, corrigir as coords e re-correr (idempotente).

## Templates incluídos

- `build-html.py` — gera a página HTML (default); mesma estrutura `ITEMS`. O favicon (lupa+check teal) está embebido como data-URI base64 (`FAVICON_B64`), por isso o `index.html` é auto-contido mesmo copiado para `/tmp`.
- `add-captions.py` — modo PIL: PNGs com legenda + markers embebidos
- `icon-512.png` / `apple-touch-icon.png` / `favicon-32.png` / `favicon-16.png` / `favicon.ico` — assets do ícone (gerados via Higgsfield). Reutilizáveis se precisares do ícone fora da página.
- `capture-ui.mjs` — script Playwright com login Supabase + screenshot helpers
- `auth-helper.sh` — helper bash para login Supabase + criação de cookie SSR

Todos copiáveis para `/tmp/<projecto>-proof/` e adaptáveis ao projecto.

## Convenções

- **Output folder**: `~/Desktop/<projecto-slug>-provas-<YYYY-MM-DD>/`
- **Nomes de ficheiro**: `NN-<descricao-kebab>.png` (NN = 01, 02, ...)
- **Status "bug"** apenas para problemas detectados durante a captura que ainda não foram corrigidos. Senão usar "ok".
- **Legenda em PT-PT**, tom directo
- Apagar o conteúdo do Desktop folder antes de regenerar (`rm -f <folder>/*.png <folder>/index.html`) para evitar restos de iterações anteriores
- Resolução: PDFs a 150 DPI; UI a viewport 1400×900 ou clip específico
