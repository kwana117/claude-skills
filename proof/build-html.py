#!/usr/bin/env python3
"""Gera uma página HTML de provas: screenshots à esquerda, painel
PEDIDO/FEITO/APROVAR à direita, bolinhas numeradas via overlay CSS.

Usa a MESMA estrutura `ITEMS` do add-captions.py — preenche uma vez e
podes correr qualquer dos dois scripts.

Diferenças vs add-captions.py:
- `markers` aqui só precisam de `n`, `x`, `y` (px na imagem original). O
  `side`/`offset` são ignorados — a bolinha fica sobre o ponto. As coords
  são convertidas para % lendo as dimensões da imagem (PIL).
- Se um item não tiver `markers`, mostra o screenshot cru + painel (mais leve).

Output: ~/Desktop/<slug>-proof-<data>/index.html + imagens copiadas para lá.
"""
from pathlib import Path
import shutil
import html as _html


FAVICON_B64 = "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"

# ---- Config (editar) --------------------------------------------------------
SRC = Path("/tmp/my-proof")                                    # onde estão os PNGs fonte
DEST = Path.home() / "Desktop" / "my-project-proof"            # pasta de output
PROJECT_TITLE = "Proof — Provas de alterações"                 # cabeçalho da página
PROJECT_DATE = "2026-01-01"                                    # mostrado no cabeçalho
PROJECT_FOOTER = "Gerado pelo skill /proof"                    # rodapé (deixar "" para esconder)

# ---- Items (mesma estrutura do add-captions.py) -----------------------------
# Exemplo genérico — substituir pelos teus items reais.
ITEMS = [
    {
        "src": "homepage-hero.png", "dst": "01-cta-button.png", "num": "1", "status": "ok",
        "pedido": 'Cliente: "O botão principal devia destacar-se mais no topo da página."',
        "feito": '(1) Botão de CTA mudado para a cor de destaque e movido acima da dobra.',
        "approve": "Aprovar cor e posição do botão, ou pedir variação.",
        "markers": [{"n": 1, "x": 480, "y": 220}],
    },
]

# ---- Render -----------------------------------------------------------------
def img_size(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.width, im.height
    except Exception:
        return None

def esc(s):
    return _html.escape(str(s))

CSS = """
:root{--bg:#f4f4f6;--card:#fff;--ink:#1d1d1f;--muted:#6b6b70;--line:#e6e6ea;
--ok:#0f786e;--ok-bg:#eafaf6;--bug:#c8321e;--bug-bg:#fdeee9;--accent:#0f786e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
header{padding:28px 32px 18px;border-bottom:1px solid var(--line);background:var(--card);
position:sticky;top:0;z-index:10;display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
header h1{font-size:20px;margin:0;font-weight:700}
header .meta{color:var(--muted);font-size:13px}
header .spacer{flex:1}
.toggle{font-size:13px;color:var(--muted);cursor:pointer;user-select:none;
border:1px solid var(--line);border-radius:8px;padding:6px 12px;background:var(--card)}
.toggle:hover{border-color:#c9c9d0}
main{max-width:1200px;margin:0 auto;padding:28px 24px 80px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;
overflow:hidden;margin-bottom:28px;display:grid;grid-template-columns:1.4fr 1fr}
.card .shot{position:relative;background:#fafafb;border-right:1px solid var(--line);
display:flex;align-items:flex-start;justify-content:center;padding:0}
.card .shot img{display:block;width:100%;height:auto}
.badge{position:absolute;transform:translate(-50%,-50%);width:30px;height:30px;
border-radius:50%;background:var(--bug);color:#fff;border:2px solid #fff;
box-shadow:0 0 0 2px rgba(200,50,30,.35),0 2px 6px rgba(0,0,0,.25);
display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px}
.panel{padding:22px 24px}
.panel .num{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:15px;
margin-bottom:14px}
.pill{font-size:12px;font-weight:600;padding:3px 10px;border-radius:999px}
.pill.ok{background:var(--ok-bg);color:var(--ok)}
.pill.bug{background:var(--bug-bg);color:var(--bug)}
.sec{margin:0 0 14px}
.sec .lbl{font-size:11px;letter-spacing:.06em;text-transform:uppercase;
color:var(--muted);font-weight:700;margin-bottom:4px}
.sec .txt{color:#2c2c30}
body.client .sec.approve{display:none}
@media(max-width:820px){.card{grid-template-columns:1fr}.card .shot{border-right:0;border-bottom:1px solid var(--line)}}
footer{text-align:center;color:var(--muted);font-size:12px;padding:24px}
"""

JS = """
const t=document.getElementById('clientToggle');
t.addEventListener('click',()=>{
  document.body.classList.toggle('client');
  t.textContent=document.body.classList.contains('client')
    ?'Modo cliente: ON (sem "o que aprovar")':'Modo cliente: OFF';
});
"""

def render_card(item):
    shot_path = SRC / item["src"]
    if not shot_path.exists():
        print(f"MISS: {shot_path}")
        return ""
    # copiar imagem para a pasta de output (referência relativa)
    out_name = item["dst"].rsplit(".", 1)[0] + Path(item["src"]).suffix
    shutil.copy(shot_path, DEST / out_name)

    badges = ""
    markers = item.get("markers", [])
    if markers:
        dims = img_size(shot_path)
        if dims:
            W, H = dims
            for m in markers:
                left = m["x"] / W * 100
                top = m["y"] / H * 100
                badges += (f'<span class="badge" style="left:{left:.2f}%;'
                           f'top:{top:.2f}%">{esc(m["n"])}</span>')
        else:
            print(f"  (sem PIL — bolinhas omitidas em {item['src']})")

    status = item.get("status", "ok")
    pill = '<span class="pill ok">Implementado</span>' if status == "ok" \
        else '<span class="pill bug">Bug a resolver</span>'

    return f"""
  <article class="card">
    <div class="shot"><img src="{esc(out_name)}" alt="{esc(item['dst'])}">{badges}</div>
    <div class="panel">
      <div class="num">#{esc(item['num'])} {pill}</div>
      <div class="sec"><div class="lbl">Pedido do cliente</div><div class="txt">{esc(item['pedido'])}</div></div>
      <div class="sec"><div class="lbl">O que foi feito</div><div class="txt">{esc(item['feito'])}</div></div>
      <div class="sec approve"><div class="lbl">O que tens de aprovar</div><div class="txt">{esc(item['approve'])}</div></div>
    </div>
  </article>"""

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    cards = "".join(render_card(it) for it in ITEMS)
    doc = f"""<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(PROJECT_TITLE)}</title>
<link rel="icon" type="image/png" href="data:image/png;base64,{FAVICON_B64}">
<style>{CSS}</style></head>
<body>
<header>
  <h1>{esc(PROJECT_TITLE)}</h1>
  <span class="meta">{esc(PROJECT_DATE)} · {len(ITEMS)} prova(s)</span>
  <span class="spacer"></span>
  <span class="toggle" id="clientToggle">Modo cliente: OFF</span>
</header>
<main>{cards}
</main>
<footer>{esc(PROJECT_FOOTER)}</footer>
<script>{JS}</script>
</body></html>"""
    out = DEST / "index.html"
    out.write_text(doc, encoding="utf-8")
    print(f"\n✓ {out}")
    print(f"  Abrir: open {out}")

if __name__ == "__main__":
    main()
