"""
generate_cards.py  – 63×88 mm cards (300 dpi)
Layer order:
  (1) pattern fill
  (2) transparent frame
  (3) artwork (95 % size + 4 px border)
Outputs RGB JPGs.
"""

import csv, os, textwrap, unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ── layout & assets ──────────────────────────────────────────────────────
DPI               = 300
CARD_W, CARD_H    = 744, 1039           # 63 × 88 mm

ART_BOX   = (64, 164, 680, 650)
TITLE_BAR = (92, 98, 652, 162)
MANA_ORG  = (600, 100)
RULES_BOX = (92, 700, 652, 930)
PT_BOX    = (542, 930, 652, 994)

ASSETS   = Path("assets")
PATTERNS = ASSETS                       # patterns live here now

TITLE_FONT_PATH  = ASSETS / "Beleren2016-Bold.ttf"
RULES_FONT_PATH  = ASSETS / "MPlantin.ttf"
SYMBOL_FONT_PATH = ASSETS / "MagicSymbols.ttf"
PARCHMENT_PATH   = ASSETS / "parchment_box.png"

# ── helpers ──────────────────────────────────────────────────────────────
def load_font(path: Path, size: int):
    try:   return ImageFont.truetype(str(path), size)
    except OSError: return ImageFont.load_default()

def slugify(txt: str):
    nfkd = unicodedata.normalize("NFKD", txt)
    ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
    return "".join(ch for ch in ascii_name if ch.isalnum()).lower()

def fit_into(box, img: Image.Image, shrink=1.0):
    bw, bh = box[2]-box[0], box[3]-box[1]
    r = min(bw/img.width, bh/img.height)*shrink
    return img.resize((int(img.width*r), int(img.height*r)), Image.LANCZOS)

def art_file(card):
    if card.get("art_file") and Path(card["art_file"]).exists():
        return Path(card["art_file"])
    slug = slugify(card["name"])
    for ext in (".png",".jpg",".jpeg"):
        p = Path("art")/f"{slug}{ext}"
        if p.exists(): return p
    raise FileNotFoundError(f"Artwork not found for {card['name']}")

# ── rendering ────────────────────────────────────────────────────────────
def draw_card(card, out_dir):
    colour = card.get("color","").lower()

    # pattern background
    pat_img = Image.open(PATTERNS/f"pattern_{colour}.png").convert("RGB")
    background = ImageOps.fit(pat_img,(CARD_W,CARD_H),Image.LANCZOS)

    # frame on top
    frame = Image.open(ASSETS/f"frame_{colour}.png").convert("RGBA")
    canvas = background.convert("RGBA")
    canvas.alpha_composite(frame)

    draw = ImageDraw.Draw(canvas)

    # fill art window with pattern first
    art_window = ImageOps.fit(pat_img,(ART_BOX[2]-ART_BOX[0], ART_BOX[3]-ART_BOX[1]),Image.LANCZOS).convert("RGBA")
    canvas.alpha_composite(art_window,(ART_BOX[0],ART_BOX[1]))

    # artwork 95 % + border
    art = Image.open(art_file(card)).convert("RGBA")
    art = fit_into(ART_BOX, art, shrink=0.95)
    ax = ART_BOX[0]+(ART_BOX[2]-ART_BOX[0]-art.width)//2
    ay = ART_BOX[1]+(ART_BOX[3]-ART_BOX[1]-art.height)//2
    canvas.alpha_composite(art,(ax,ay))
    draw.rectangle([ax-2, ay-2, ax+art.width+1, ay+art.height+1],
                   outline="black", width=4)

    # parchment rules box
    if PARCHMENT_PATH.exists():
        parch = ImageOps.fit(Image.open(PARCHMENT_PATH).convert("RGBA"),
                             (RULES_BOX[2]-RULES_BOX[0], RULES_BOX[3]-RULES_BOX[1]),
                             Image.LANCZOS)
        canvas.alpha_composite(parch,(RULES_BOX[0],RULES_BOX[1]))

    # fonts
    t_font = load_font(TITLE_FONT_PATH, 60)
    r_font = load_font(RULES_FONT_PATH, 34)
    s_font = load_font(SYMBOL_FONT_PATH, 44)
    meas   = ImageDraw.Draw(Image.new("RGB",(1,1))).textlength

    title, max_w = card["name"].upper(), TITLE_BAR[2]-TITLE_BAR[0]-8
    while meas(title,font=t_font) > max_w and t_font.size>28:
        t_font = load_font(TITLE_FONT_PATH, t_font.size-2)
    tx = TITLE_BAR[0] + (max_w - meas(title,t_font))//2 + 4
    ty = TITLE_BAR[1] + (TITLE_BAR[3]-TITLE_BAR[1]-t_font.size)//2
    draw.text((tx,ty), title, font=t_font, fill="white",
              stroke_width=2, stroke_fill="black")

    draw.text(MANA_ORG, card.get("cost",""), font=s_font,
              fill="white", stroke_width=1, stroke_fill="black")

    if card.get("type","").lower()=="creature":
        pw = card.get("power",card.get("strength",""))
        tg = card.get("toughness",pw)
        rules = f"{card.get('subtype','').title()} — {pw}/{tg}"
    else:
        rules = card.get("description","")
    draw.multiline_text((RULES_BOX[0]+8,RULES_BOX[1]+8),
                        textwrap.fill(rules,40),
                        font=r_font, fill="black", spacing=4)

    # P/T square pattern + outline
    pt_pat = ImageOps.fit(pat_img,(PT_BOX[2]-PT_BOX[0],PT_BOX[3]-PT_BOX[1]),Image.LANCZOS).convert("RGBA")
    canvas.alpha_composite(pt_pat, (PT_BOX[0],PT_BOX[1]))
    draw.rectangle(PT_BOX, outline="black", width=2)

    # save JPG
    out = canvas.convert("RGB")
    out_path = Path(out_dir)/f"{slugify(card['name'])}.jpg"
    out.save(out_path, dpi=(DPI,DPI), quality=95, optimize=True, progressive=True)
    print("Saved", out_path)

# ── CSV driver ───────────────────────────────────────────────────────────
def main(csv_path,out_dir):
    os.makedirs(out_dir,exist_ok=True)
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            draw_card(row,out_dir)

if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        print("Usage: python generate_cards.py <cards.csv> <output_dir>")
        raise SystemExit(1)
    main(sys.argv[1],sys.argv[2])
