import csv
import os
import unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

DPI = 300
CARD_W, CARD_H = (744, 1039)  # 63x88 mm trimmed

# Layout coordinates (match the frame assets)
ART_BOX = (64, 164, 680, 650)
TITLE_ORIGIN = (92, 98)
COST_ORIGIN = (600, 100)
TEXT_BOX = (92, 700, 652, 960)

ASSETS_DIR = Path("assets")
TITLE_FONT_PATH = os.environ.get("TITLE_FONT", ASSETS_DIR / "Beleren-Bold.ttf")
RULES_FONT_PATH = os.environ.get("RULES_FONT", ASSETS_DIR / "MPlantin.ttf")
SYMBOL_FONT_PATH = os.environ.get("SYMBOL_FONT", ASSETS_DIR / "MagicSymbols.ttf")


def load_font(path: str | Path, size: int) -> ImageFont.FreeTypeFont:
    """Load a font, falling back to the default if the file is missing."""
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def fit_into(box, img: Image.Image) -> Image.Image:
    """Resize *img* to cover ``box`` while preserving aspect ratio."""
    bw, bh = box[2] - box[0], box[3] - box[1]
    ratio = min(bw / img.width, bh / img.height)
    return img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)


def slugify(name: str) -> str:
    """Return an ASCII file name derived from ``name``."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
    return "".join(ch for ch in ascii_name if ch.isalnum()).lower()


def resolve_art_file(card: dict) -> Path:
    """Determine the artwork path for a card."""
    if card.get("art_file") and Path(card["art_file"]).exists():
        return Path(card["art_file"])
    slug = slugify(card["name"])
    for ext in (".png", ".jpg", ".jpeg"):  # search in art folder
        candidate = Path("art") / f"{slug}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Artwork not found for {card['name']}")


def draw_card(card: dict, out_dir: str) -> None:
    color = card.get("color", "").lower()
    frame_path = ASSETS_DIR / f"frame_{color}.png"
    if not frame_path.exists():
        frame_path = ASSETS_DIR / "frame.png"
    FRAME = Image.open(frame_path).convert("RGBA") if frame_path.exists() else Image.new(
        "RGBA", (CARD_W, CARD_H), "white"
    )

    canvas = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    canvas.paste(FRAME, (0, 0), FRAME)

    art_img = Image.open(resolve_art_file(card)).convert("RGBA")
    art_img = fit_into(ART_BOX, art_img)
    ax = ART_BOX[0] + (ART_BOX[2] - ART_BOX[0] - art_img.width) // 2
    ay = ART_BOX[1] + (ART_BOX[3] - ART_BOX[1] - art_img.height) // 2
    canvas.paste(art_img, (ax, ay), art_img)

    draw = ImageDraw.Draw(canvas)
    title_font = load_font(TITLE_FONT_PATH, 48)
    rules_font = load_font(RULES_FONT_PATH, 34)
    symbol_font = load_font(SYMBOL_FONT_PATH, 44)

    draw.text(TITLE_ORIGIN, card["name"].upper(), font=title_font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(COST_ORIGIN, card.get("cost", ""), font=symbol_font, fill="white", stroke_width=1, stroke_fill="black")

    if card.get("type", "").lower() == "creature":
        strength = card.get("stregth", "")
        toughness = card.get("toughness", strength)
        raw = f"{card.get('subtype', '')} — {strength}/{toughness}"
    else:
        raw = card.get("description", "")
    wrapped = "\n".join(textwrap.wrap(str(raw), width=38))
    draw.multiline_text((TEXT_BOX[0], TEXT_BOX[1]), wrapped, font=rules_font, fill="black", spacing=4)

    out_img = canvas.convert("CMYK")
    out_path = Path(out_dir) / f"{slugify(card['name'])}.tif"
    out_img.save(out_path, dpi=(DPI, DPI), compression="tiff_lzw")
    print("Saved", out_path)


def main(csv_path: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            draw_card(row, out_dir)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python generate_cards.py <cards.csv> <output_dir>")
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2])
