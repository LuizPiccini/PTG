"""
generate_cards.py – 63×88 mm cards (300 dpi)
Uses 32×32 PNG icons (assets/symbols/) for power and cost. CSV fields
`power_symbol` and `cost_symbol` hold space‑separated icon names.
Changes in this revision
• blank line between cost row and flavour text
• first label is “Poder:” when type=="Creature" else “Efeito:”
"""

import csv
import os
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps

# ── layout & assets ──────────────────────────────────────────────────────
DPI = 300
CARD_W, CARD_H = 744, 1039  # 63 × 88 mm
EXPORT_W, EXPORT_H = 815, 1110      # 69 × 94 mm (with bleed) 
TITLE_FONT_PT  = 9          # ≈50 pt @300 dpi

ART_BOX      = (64, 164, 680, 650)
TITLE_BAR    = (92, 98, 652, 162)
SUBTITLE_BAR = (92, 650, 652, 700)
RULES_BOX    = (92, 700, 652, 930)
TITLE_Y_PAD    = 14
SUBTITLE_Y_PAD = 10

ASSETS    = Path("assets")
PATTERNS  = ASSETS
ICONS_DIR = ASSETS  # 32×32 PNGs

TITLE_FONT_PATH   = ASSETS / "Beleren2016-Bold.ttf"
RULES_FONT_PATH   = ASSETS / "MPlantin.ttf"
RULES_FONT_ITALIC = ASSETS / "MPlantin-Italic.ttf"
PARCHMENT_PATH    = ASSETS / "parchment_box.png"

ICON_SIZE = 32

# ── helpers ──────────────────────────────────────────────────────────────

def pt_to_px(pt: int) -> int:
    return round(pt * DPI / 72)


def load_font(path: Path, size: int):
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        print(f"[warn] font not found: {path}")
        return ImageFont.load_default()


def slugify(txt: str) -> str:
    norm = unicodedata.normalize("NFKD", txt)
    return "".join(c for c in norm if unicodedata.category(c)[0] != "M" and c.isalnum()).lower()


def fit_into(box, img: Image.Image, shrink=1.0) -> Image.Image:
    bw, bh = box[2]-box[0], box[3]-box[1]
    r = min(bw/img.width, bh/img.height) * shrink
    return img.resize((int(img.width*r), int(img.height*r)), Image.LANCZOS)


def art_path(card) -> Path:
    if card.get("art_file") and Path(card["art_file"]).exists():
        return Path(card["art_file"])
    slug = slugify(card["name"])
    for ext in (".png", ".jpg", ".jpeg"):
        p = Path("art")/f"{slug}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"Artwork not found for {card['name']}")


@lru_cache(maxsize=None)
def load_icon(name: str) -> Optional[Image.Image]:
    if not name:
        return None
    path = ICONS_DIR / (name if name.endswith(".png") else f"{name}.png")
    if not path.exists():
        print(f"[warn] icon missing: {path}")
        return None
    return Image.open(path).convert("RGBA").resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)


def draw_icon_row(canvas: Image.Image, tokens: str, x: int, y: int):
    for tok in tokens.split():
        icon = load_icon(tok)
        if icon:
            canvas.alpha_composite(icon, (x, y))
            x += ICON_SIZE + 2


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line+" "+w).strip()
        if font.getlength(test) <= max_w:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines

# ── rendering ────────────────────────────────────────────────────────────

def draw_card(card: dict, out_dir: str):
    colour = card.get("color", "").lower()
    bg = ImageOps.fit(Image.open(PATTERNS/f"pattern_{colour}.png"), (CARD_W,CARD_H), Image.LANCZOS).convert("RGBA")
    frame = Image.open(ASSETS/f"frame_{colour}.png").convert("RGBA")
    canvas = Image.alpha_composite(bg, frame)
    draw   = ImageDraw.Draw(canvas)

    art = fit_into(ART_BOX, Image.open(art_path(card)).convert("RGBA"), 0.95)
    ax = ART_BOX[0] + (ART_BOX[2]-ART_BOX[0]-art.width)//2
    ay = ART_BOX[1] + (ART_BOX[3]-ART_BOX[1]-art.height)//2
    canvas.alpha_composite(art, (ax, ay))
    draw.rectangle([ax-2, ay-2, ax+art.width+1, ay+art.height+1], outline="black", width=4)

    if PARCHMENT_PATH.exists():
        parch = ImageOps.fit(Image.open(PARCHMENT_PATH), (RULES_BOX[2]-RULES_BOX[0], RULES_BOX[3]-RULES_BOX[1]), Image.LANCZOS).convert("RGBA")
        canvas.alpha_composite(parch, (RULES_BOX[0], RULES_BOX[1]))

    title_font   = load_font(TITLE_FONT_PATH, pt_to_px(TITLE_FONT_PT))
    subtitle_font= load_font(TITLE_FONT_PATH, 32)
    base_font    = load_font(RULES_FONT_PATH, 32)
    italic_font  = load_font(RULES_FONT_ITALIC if RULES_FONT_ITALIC.exists() else RULES_FONT_PATH, 28)

    draw.text((TITLE_BAR[0]+8, TITLE_BAR[1]+ TITLE_Y_PAD), card["name"].upper(), font=title_font, fill="white", stroke_width=2, stroke_fill="black")
    if card.get("subtitle"):
        draw.text((SUBTITLE_BAR[0]+8, SUBTITLE_BAR[1]+ SUBTITLE_Y_PAD), card["subtitle"], font=subtitle_font, fill="white", stroke_width=2, stroke_fill="black")

    x = RULES_BOX[0]+16
    y = RULES_BOX[1]+20
    gap = 6
    max_w = RULES_BOX[2]-RULES_BOX[0]-32

    # Label depends on type
    label = "Poder:" if card.get("type", "").lower()=="creature" else "Efeito:"
    draw.text((x, y), label, font=base_font, fill="black")
    draw_icon_row(canvas, card.get("power_symbol", ""), x + int(base_font.getlength(label)) + 8, y-4)
    y += base_font.size + gap*2

    draw.text((x, y), "Custo:", font=base_font, fill="black")
    draw_icon_row(canvas, card.get("cost_symbol", ""), x + int(base_font.getlength("Custo:")) + 8, y-4)
    y += base_font.size + gap*6  # extra blank line before flavour

    for ln in wrap_text(card.get("flavor_text", ""), italic_font, max_w):
        draw.text((x, y), ln, font=italic_font, fill="black")
        y += italic_font.size + gap

    out_path = Path(out_dir)/f"{slugify(card['name'])}.jpg"
    export_img = canvas.resize((EXPORT_W, EXPORT_H), Image.LANCZOS)
    export_img.convert("CMYK").save(
        out_path, dpi=(DPI, DPI), quality=95, optimize=True, progressive=True)
    print("Saved", card["name"])


# ── CSV driver ────────────────────────────────────────────────────────────

def main(csv_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            draw_card(row, out_dir)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python generate_cards.py <cards.csv> <output_dir>")
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2])
