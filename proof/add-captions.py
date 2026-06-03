#!/usr/bin/env python3
"""Adiciona caixa de caption + marcadores numerados a cada screenshot."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import textwrap

SRC = Path("/tmp/my-proof")
DEST = Path.home() / "Desktop" / "my-project-proof"
DEST.mkdir(exist_ok=True)

FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
def get_font(size):
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_bold(size):
    for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return get_font(size)

# Markers use ABSOLUTE pixel coordinates in the ORIGINAL screenshot image
# (before any padding/expansion). The script translates to centered coords for narrow images.
# Exemplo genérico — substituir pelos teus items reais.
ITEMS = [
    {
        "src": "homepage-hero.png", "dst": "01-cta-button.png", "num": "1", "status": "ok",
        "pedido": 'Cliente: "O botão principal devia destacar-se mais no topo da página."',
        "feito": '(1) Botão de CTA mudado para a cor de destaque e movido acima da dobra.',
        "approve": "Aprovar cor e posição do botão, ou pedir variação.",
        "markers": [{"n": 1, "x": 480, "y": 220, "side": "above"}],
    },
    {
        "src": "footer.png", "dst": "02-footer-links.png", "num": "2", "status": "ok",
        "pedido": 'Cliente: "Adicionar os links das redes sociais no rodapé."',
        "feito": '(1) Ícones de Instagram e LinkedIn adicionados à direita do rodapé.',
        "approve": "Confirmar quais redes incluir e a ordem.",
        "markers": [
            {"n": 1, "x": 660, "y": 50, "side": "above"},   # social icons on the right
        ],
    },
]

def draw_marker(draw, anchor_x, anchor_y, n, scale=1.0, side="left", offset=None, img_size=None):
    """Draw a numbered badge OFFSET from (anchor_x, anchor_y) with an arrow pointing at the anchor.
    The badge never covers the anchor element."""
    r = int(22 * scale)
    if offset is None:
        offset = int(110 * scale)

    # Compute badge centre based on side
    if side == "left":
        bx, by = anchor_x - offset, anchor_y
    elif side == "right":
        bx, by = anchor_x + offset, anchor_y
    elif side == "above":
        bx, by = anchor_x, anchor_y - offset
    elif side == "below":
        bx, by = anchor_x, anchor_y + offset
    else:
        bx, by = anchor_x - offset, anchor_y

    # Clamp badge into image bounds (with a margin)
    if img_size is not None:
        W, H = img_size
        margin = r + int(8 * scale)
        bx = max(margin, min(W - margin, bx))
        by = max(margin, min(H - margin, by))

    # Arrow: line from badge edge to a point slightly before the anchor (don't touch it)
    import math
    dx, dy = anchor_x - bx, anchor_y - by
    dist = math.hypot(dx, dy) or 1
    ux, uy = dx / dist, dy / dist
    # Stop the arrow short of the anchor so it doesn't touch the element
    arrow_gap = int(14 * scale)
    end_x = anchor_x - ux * arrow_gap
    end_y = anchor_y - uy * arrow_gap
    # Start from the badge edge (not its centre)
    start_x = bx + ux * r
    start_y = by + uy * r

    arrow_color = (220, 50, 30)
    # Line (slightly thick) with subtle white halo for legibility on dark backgrounds
    halo_w = max(5, int(7 * scale))
    line_w = max(3, int(4 * scale))
    draw.line([(start_x, start_y), (end_x, end_y)], fill=(255, 255, 255), width=halo_w)
    draw.line([(start_x, start_y), (end_x, end_y)], fill=arrow_color, width=line_w)

    # Arrowhead at the (end_x, end_y) — small filled triangle
    head_len = int(16 * scale)
    head_w = int(10 * scale)
    # Perpendicular vector
    px, py = -uy, ux
    base_x = end_x - ux * head_len
    base_y = end_y - uy * head_len
    p1 = (end_x, end_y)
    p2 = (base_x + px * head_w, base_y + py * head_w)
    p3 = (base_x - px * head_w, base_y - py * head_w)
    draw.polygon([p1, p2, p3], fill=arrow_color, outline=(255, 255, 255))

    # White halo around badge, then red filled circle with white border
    halo_r = r + int(4 * scale)
    draw.ellipse([bx - halo_r, by - halo_r, bx + halo_r, by + halo_r], fill=(255, 255, 255), outline=(255, 255, 255))
    draw.ellipse([bx - r, by - r, bx + r, by + r], fill=arrow_color, outline=(255, 255, 255), width=max(2, int(3 * scale)))
    # White number
    font = get_bold(int(24 * scale))
    text = str(n)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((bx - tw // 2 - bbox[0], by - th // 2 - bbox[1]), text, font=font, fill="white")

def render_caption(width, item):
    scale = max(1.0, width / 900)
    pad_x, pad_y = int(28 * scale), int(22 * scale)
    body_size = int(15 * scale)
    label_size = int(13 * scale)
    title_size = int(20 * scale)
    line_h = int(body_size * 1.5)
    title_h = int(title_size * 1.4)

    body_font = get_font(body_size)
    label_font = get_bold(label_size)
    title_font = get_bold(title_size)

    char_w = int(body_size * 0.6)
    max_chars = max(40, (width - 2 * pad_x) // char_w)

    sections = [
        ("PEDIDO DO CLIENTE", item["pedido"]),
        ("O QUE FOI FEITO", item["feito"]),
        ("O QUE TENS DE APROVAR", item["approve"]),
    ]
    lines_total = 0
    section_lines = []
    for label, text in sections:
        wrapped = textwrap.wrap(text, width=max_chars)
        section_lines.append((label, wrapped))
        lines_total += 1 + len(wrapped) + 1

    height = pad_y * 2 + title_h + lines_total * line_h

    bg = (255, 255, 255) if item["status"] == "ok" else (255, 245, 240)
    accent = (15, 120, 110) if item["status"] == "ok" else (200, 50, 30)

    cap = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(cap)

    border_h = max(4, int(4 * scale))
    d.rectangle([0, 0, width - 1, border_h], fill=accent)

    title_text = f'#{item["num"]} — ' + ("Implementado" if item["status"] == "ok" else "Bug a resolver")
    d.text((pad_x, pad_y), title_text, font=title_font, fill=accent)

    y = pad_y + title_h + 4
    for label, wrapped in section_lines:
        d.text((pad_x, y), label, font=label_font, fill=(80, 80, 80))
        y += line_h
        for line in wrapped:
            d.text((pad_x, y), line, font=body_font, fill=(40, 40, 40))
            y += line_h
        y += line_h - 18

    d.rectangle([0, border_h, border_h, height - 1], fill=accent)
    return cap

def process(item):
    src_path = SRC / item["src"]
    if not src_path.exists():
        print(f"MISS: {src_path}")
        return
    img = Image.open(src_path).convert("RGB")
    orig_w, orig_h = img.width, img.height

    # Draw markers in original coords first (before any padding)
    marker_scale = max(0.8, orig_w / 900)
    d = ImageDraw.Draw(img)
    for m in item.get("markers", []):
        draw_marker(
            d, m["x"], m["y"], m["n"],
            scale=marker_scale,
            side=m.get("side", "left"),
            offset=m.get("offset"),
            img_size=(orig_w, orig_h),
        )

    # Pad narrow images to readable width
    target_w = max(orig_w, 900)
    if orig_w < target_w:
        bg = Image.new("RGB", (target_w, orig_h), (245, 245, 247))
        bg.paste(img, ((target_w - orig_w) // 2, 0))
        img = bg

    W = img.width
    caption = render_caption(W, item)
    gap = max(60, int(W * 0.06))
    total_h = img.height + gap + caption.height
    final = Image.new("RGB", (W, total_h), (245, 245, 247))
    final.paste(img, (0, 0))
    final.paste(caption, (0, img.height + gap))
    out = DEST / item["dst"]
    final.save(out)
    print(f"✓ {item['dst']} ({W}×{total_h})")

for item in ITEMS:
    process(item)

print(f"\nDone → {DEST}")
