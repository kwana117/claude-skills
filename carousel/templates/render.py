#!/usr/bin/env python3
"""
render.py — Carousel PNG renderer
Gerado pelo skill /carousel. Playwright → slides/*.png
SCALE=1 obrigatório (limite 2000px do Claude).
"""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

HERE  = Path(__file__).parent
HTML  = HERE / "index.html"
OUT   = HERE / "slides"
PLAN  = HERE / "plan.json"
OUT.mkdir(exist_ok=True)

SCALE = 1
W, H  = 1080, 1350
assert W * SCALE <= 2000 and H * SCALE <= 2000, \
    "Output must stay <=2000px (Claude image limit). Reduce SCALE."

def slide_count():
    with open(PLAN) as f:
        return len(json.load(f)["slides"])

async def main():
    n = slide_count()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=SCALE,
        )
        page = await ctx.new_page()
        await page.goto(f"file://{HTML}")

        # 1) Aguardar fonts.ready
        await page.evaluate("document.fonts.ready")

        # 2) Forçar pré-load explícito de TODAS as variantes serif/italic usadas.
        # Sem isto, slides com quote italic podem renderizar como caixa cinzenta sólida
        # (font face italic ainda não está carregada quando o screenshot é tirado).
        # Cobrir os tamanhos típicos: capa (156), L3 headline (78), L2 quote (70),
        # L6 headline (64), L3 parallel (38). Pesos: 400 italic + 500 roman.
        await page.evaluate("""
            Promise.all([
                document.fonts.load('italic 400 156px "Cormorant Garamond"'),
                document.fonts.load('italic 400 78px "Cormorant Garamond"'),
                document.fonts.load('italic 400 70px "Cormorant Garamond"'),
                document.fonts.load('italic 400 64px "Cormorant Garamond"'),
                document.fonts.load('italic 400 38px "Cormorant Garamond"'),
                document.fonts.load('500 156px "Cormorant Garamond"'),
                document.fonts.load('500 78px "Cormorant Garamond"'),
                document.fonts.load('500 70px "Cormorant Garamond"'),
                document.fonts.load('500 64px "Cormorant Garamond"'),
                document.fonts.load('600 70px "Cormorant Garamond"'),
                document.fonts.load('600 64px "Cormorant Garamond"'),
                document.fonts.load('italic 600 70px "Cormorant Garamond"'),
                document.fonts.load('italic 600 64px "Cormorant Garamond"'),
                document.fonts.load('300 24px "DM Sans"'),
                document.fonts.load('400 18px "DM Sans"'),
                document.fonts.load('500 14px "DM Sans"')
            ])
        """)

        # 3) Buffer adicional para layout final estabilizar
        await page.wait_for_timeout(2500)

        for i in range(1, n + 1):
            sel = f"#slide-{i}"
            el  = await page.query_selector(sel)
            if not el:
                print(f"MISS {sel}")
                continue
            out = OUT / f"slide-{i:02d}.png"
            await el.screenshot(path=str(out))
            print(f"OK  {out.name}")

        await browser.close()
        print(f"\nDone — {n} slides em {OUT}/")

asyncio.run(main())
