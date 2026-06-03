---
name: classifier-dashboard
description: Build an interactive drag-and-drop classifier dashboard (HTML + Python server) for triaging large lists of items into buckets. Pattern proven for organizing files/folders/zips, but reusable for ANY many-to-few categorization task — clients, leads, tasks, ideas, content, contacts. User accepts auto-suggestions or drags to override; saves to JSON for downstream execution. Use when user needs to classify >20 items into a fixed taxonomy AND text-based questionnaire would be too slow.
---

# Classifier Dashboard — Pattern reutilizável

Quando o utilizador tem **dezenas a centenas de items** para classificar em **categorias fixas**, mas não quer fazer um questionário linear, esta dashboard browser-based dá-lhe **drag-and-drop visual** com pré-sugestões inteligentes. Foi inventada para reorganizar 2.5 TB do Vault WD My Book (Maio 2026, 3 rondas, 163 moves) e é reutilizável para qualquer triagem.

## Quando usar

✅ User tem **20+ items** a categorizar
✅ Categorias são **conhecidas** ou descobríveis (clientes, projectos, tags)
✅ Decisão por item é **rápida visualmente** mas escolha tem que ser do user
✅ Pattern matching de nomes consegue **pré-sugerir 60-80%** das classificações
✅ Outputs alimentam **execução automatizada** depois (moves, updates, etc.)

❌ NÃO usar para: classificações com poucas opções (use AskUserQuestion); items que precisam ser lidos individualmente; quando a decisão é multidimensional (mais que bucket + opcional subname)

## Arquitectura

```
┌─────────────────────┐         ┌──────────────────────┐
│ MacBook (browser)   │ ──GET── │ Python http.server   │
│ http://localhost:N  │         │ (localhost only)     │
│  drag+drop HTML/JS  │ ──POST  │ - GET /data → items  │
│  localStorage cache │         │ - GET / → HTML       │
└─────────────────────┘         │ - POST /save → JSON  │
                                └──────────┬───────────┘
                                           ▼
                          /tmp/vault-classify-data.json (input)
                          /tmp/vault-classify.json     (output)
```

**Estado:** localStorage para draft → SAVE escreve JSON local → script downstream consome.

## 3 ficheiros que compõem o pattern

### 1. Gather script (Python, recolhe items + faz pré-sugestões)

Corre **na máquina onde os items vivem** (localmente, ou via SSH no host onde os ficheiros estão).

```python
import os, json, subprocess

PATTERNS = [
  # (substring_no_nome_minusculo, bucket_destino)
  ('invoices',      'Finance/Invoices'),
  ('contract',      'Legal/Contracts'),
  ('receipt',       'Finance/Receipts'),
  ('untitled',      '_backlog'),
  # ... dezenas/centenas de patterns específicos do domínio
]

def suggest(name):
    low = name.lower()
    for pat, dst in PATTERNS:
        if pat in low: return dst
    return None

def gather(path, parent_rel):
    """Recolhe size, file count, sample de entries, suggestion."""
    if not os.path.exists(path): return None
    is_dir = os.path.isdir(path)
    name = os.path.basename(path)
    if is_dir:
        size = subprocess.run(['du','-sh',path], capture_output=True).stdout.split()[0].decode()
        files = subprocess.run(['find', path, '-type', 'f'], capture_output=True).stdout.count(b'\n')
        entries = sorted(os.listdir(path))[:8]
        # Escapar control chars (newlines em nomes de ficheiro existem)
        entries = [''.join(c if (c.isprintable() or c==' ') else '?' for c in e) for e in entries]
    else:
        sz = os.path.getsize(path)
        size = f'{sz/1024/1024:.0f}M' if sz < 1e9 else f'{sz/1024/1024/1024:.1f}G'
        files, entries = 1, []
    return {
        'path': f'{parent_rel}/{name}',
        'size': size,
        'files': files,
        'sample': entries,
        'is_file': not is_dir,
        'suggestion': suggest(name),  # bucket_id ou None
    }

# Recolher os items que queres classificar
data = []
for name in sorted(os.listdir('/path/to/source')):
    item = gather(os.path.join('/path/to/source', name), 'source-rel')
    if item: data.append(item)

with open('/tmp/classify-data.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

sug = sum(1 for d in data if d.get('suggestion'))
print(f'{len(data)} items ({sug} com sugestões)')
```

### 2. Server (Python http.server, na máquina do user)

Único ficheiro, sem dependências externas. Serve HTML, /data (lê JSON), /save (escreve JSON).

```python
#!/usr/bin/env python3
import http.server, json
PORT = 8766
DATA_FILE = "/tmp/classify-data.json"
OUTPUT_FILE = "/tmp/classify-output.json"

HTML = r"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="utf-8"><title>Classifier</title>
<style>
  /* dark theme com cards + drop zones */
  body { font-family: -apple-system, system-ui, sans-serif; background: #0a0a0a; color: #e8e8e8; padding: 16px; }
  .layout { display: grid; grid-template-columns: 1fr 1.3fr; gap: 16px; height: calc(100vh - 80px); }
  .col-body { overflow-y: auto; background: #111; border: 1px solid #222; border-radius: 8px; padding: 12px; }
  .card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 10px; margin-bottom: 8px; cursor: grab; }
  .card.dragging { opacity: 0.3; }
  .bucket { background: #161616; border: 2px dashed #2a2a2a; border-radius: 6px; padding: 8px; min-height: 50px; }
  .bucket.drag-over { background: #f9731620; border-color: #f97316; }
  .bucket-item.suggested { background: #6366f120; border-left: 2px solid #6366f1; }  /* ✨ azul para sugestões pré-aplicadas */
  .btn { background: #f97316; color: #fff; border: none; border-radius: 6px; padding: 10px 18px; cursor: pointer; }
</style>
</head>
<body>
  <h1>Classifier</h1>
  <div class="layout">
    <div><div id="folders" class="col-body"></div></div>
    <div>
      <div id="destinations" class="col-body"></div>
      <button class="btn" id="btnSave">💾 Save</button>
      <button class="btn" id="btnAccept">✓ Aceitar todas sugestões</button>
    </div>
  </div>
<script>
const BUCKETS = [
  {id: "Finance/Invoices",  label: "Finance / Invoices"},
  {id: "Legal/Contracts",   label: "Legal / Contracts"},
  {id: "_backlog",          label: "❓ _backlog"},
  // ... DEFAULT_SECTIONS agrupadas; suportar add-bucket dinâmico via prompt()
];

let folders = [];
let classifications = JSON.parse(localStorage.getItem("classify") || "{}");

function el(tag, props, ...kids) {
  const e = document.createElement(tag);
  Object.assign(e, props || {});
  for (const k of kids) {
    if (k == null) continue;
    if (typeof k === "string") e.appendChild(document.createTextNode(k));
    else e.appendChild(k);
  }
  return e;
}

function persist() { localStorage.setItem("classify", JSON.stringify(classifications)); }

function applySuggestions() {
  folders.forEach(f => {
    if (f.suggestion && !classifications[f.path]) {
      classifications[f.path] = { bucket: f.suggestion, suggested: true };
    }
  });
  persist();
}

function renderFolders() {
  const wrap = document.getElementById("folders");
  wrap.replaceChildren();
  folders.forEach(f => {
    if (classifications[f.path]) return;
    const card = el("div", {className: "card", draggable: true});
    card.dataset.path = f.path;
    card.appendChild(el("div", {textContent: f.path}));
    card.appendChild(el("div", {textContent: `${f.size} · ${f.files}`}));
    card.addEventListener("dragstart", e => { e.dataTransfer.setData("text/plain", f.path); card.classList.add("dragging"); });
    card.addEventListener("dragend", () => card.classList.remove("dragging"));
    wrap.appendChild(card);
  });
}

function renderDestinations() {
  const wrap = document.getElementById("destinations");
  wrap.replaceChildren();
  BUCKETS.forEach(b => {
    const items = Object.entries(classifications).filter(([k,v]) => v.bucket === b.id);
    const bel = el("div", {className: "bucket"});
    bel.appendChild(el("div", {textContent: `${b.label} (${items.length})`}));
    items.forEach(([k,v]) => {
      const row = el("div", {className: "bucket-item" + (v.suggested ? " suggested" : "")});
      row.appendChild(el("span", {textContent: (v.suggested ? "✨ " : "") + k}));
      const x = el("button", {textContent: "×"});
      x.onclick = () => { delete classifications[k]; persist(); renderAll(); };
      row.appendChild(x);
      bel.appendChild(row);
    });
    bel.addEventListener("dragover", e => { e.preventDefault(); bel.classList.add("drag-over"); });
    bel.addEventListener("dragleave", () => bel.classList.remove("drag-over"));
    bel.addEventListener("drop", e => {
      e.preventDefault(); bel.classList.remove("drag-over");
      const path = e.dataTransfer.getData("text/plain");
      classifications[path] = { bucket: b.id, suggested: false };
      persist(); renderAll();
    });
    wrap.appendChild(bel);
  });
}

function renderAll() { renderFolders(); renderDestinations(); }

document.getElementById("btnSave").onclick = async () => {
  await fetch("/save", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(classifications)});
};
document.getElementById("btnAccept").onclick = () => {
  Object.keys(classifications).forEach(k => { if (classifications[k].suggested) classifications[k].suggested = false; });
  persist(); renderAll();
};

(async function load() {
  folders = await (await fetch("/data")).json();
  if (Object.keys(classifications).length === 0) applySuggestions();
  renderAll();
})();
</script>
</body>
</html>
"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        elif self.path == "/data":
            with open(DATA_FILE) as f:
                data = json.load(f)
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length",0))
            body = self.rfile.read(length).decode("utf-8")
            with open(OUTPUT_FILE,"w") as f:
                json.dump(json.loads(body), f, indent=2, ensure_ascii=False)
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true}')
    def log_message(self, *a, **k): pass

http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
```

### 3. Downstream executor (lê JSON, executa)

Script que pega na `classify-output.json` e age:
- Para reorganização de files: `shutil.move(src, dst)` com manifest reversível
- Para CRM: API calls
- Para tasks: scheduling
- Pattern: sempre **dry-run primeiro** → user confirma → execute com manifest

Exemplo do que fizemos no Vault:
```python
with open('/tmp/classify-output.json') as f:
    classifications = json.load(f)

MOVES = []
for src, info in classifications.items():
    base = os.path.basename(src)
    dst = f"{info['bucket']}/{base}"
    MOVES.append((src, dst))

# Auto-suffix se destino já existe
if os.path.exists(dst_full):
    category = src.split('/')[-2]
    dst = f"{dst}-from-{category}"
```

## Lições aprendidas (gotchas)

1. **localStorage key versionada** (`classify-r1`, `classify-r2`, `classify-r3`) — quando refaz dashboard com items novos, evita misturar com classificações anteriores
2. **Marcar sugestões visualmente** com cor distinta (✨ azul vs cinza) — user vê de relance o que é proposta vs própria escolha
3. **Botão "Aceitar todas sugestões"** — quando user revisou e está confortável, um clique compromete tudo
4. **Buckets dinâmicos** — campo "+ novo" + "+ Nova secção" para user criar destinos não previstos
5. **Sample preview** — toggle "▸ Sample files" mostra os primeiros 8 items dentro de pastas para context
6. **Filename Control characters** — `find` + nomes podem ter `\n`/`\t` literais; sempre filtrar com `''.join(c if (c.isprintable() or c==' ') else '?' for c in name)` antes de meter em JSON
7. **Single Python file** — sem framework, sem dependências, sem build step. Corre com `python3 server.py`. Browser abre `http://localhost:PORT`
8. **Pre-suggestions via pattern matching** — uma lista de `(substring, bucket)` resolve 60-80% dos casos. User só toca no resto.
9. **Cache SSH leituras pesadas** — se dashboard puxa dados de máquina remota, cachear no Python server (TTL 2-5s)
10. **Auto-suffix em conflitos de destino** — quando 5 items diferentes tentam ir para o mesmo path, sufixar com o contexto de origem (`-from-Áudio`, `-from-Documentos`, `-from-ZIPs`)

## Como instanciar

1. Identifica taxonomia (buckets pré-definidos por secção)
2. Lista patterns de auto-sugestão para domínio específico
3. Adapta o gather script à fonte de dados
4. Copia o server boilerplate, ajusta `BUCKETS` e `DEFAULT_SECTIONS` no JS
5. Lança: `python3 server.py` + `open http://localhost:8766`
6. User classifica, clica Save → JSON em `/tmp/classify-output.json`
7. Constrói executor downstream específico ao domínio

## Casos de uso futuros

- Triagem **clientes** ativo/inactivo/arquivo
- Categorização de **leads** por estágio do funil
- Decidir **tasks** entre projects/dia/semana/backlog
- Organizar **bookmarks/inbox** por área
- Classificar **emails** por intent (action / FYI / archive)
- Decidir **content ideas** por pillar / tier
- Atribuir **contactos** a sectores

A página `http://localhost:PORT` é o standard interface — visual, rápido, persistente em localStorage, save explícito em endpoint.
