import csv
import os
from PIL import Image, ImageDraw, ImageFont

# Trimmed card size (63x88mm at 300 DPI)
TRIM_WIDTH = 744
TRIM_HEIGHT = 1039

# Full card size including 3mm bleed on each side (69x94mm at 300 DPI)
BLEED = 35  # ~3mm
CARD_WIDTH = TRIM_WIDTH + BLEED * 2 + 1
CARD_HEIGHT = TRIM_HEIGHT + BLEED * 2 + 1
DPI = 300

COLOR_MAP = {
    'white': '#e6e6e6',
    'blue': '#99ccff',
    'black': '#404040',
    'red': '#ff9999',
    'green': '#99ff99'
}

TITLE_FONT = os.environ.get(
    "TITLE_FONT",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
TEXT_FONT = os.environ.get(
    "TEXT_FONT",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font, falling back to the default if the file is missing."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def draw_card(card: dict, output_dir: str) -> None:
    """Render a single card as an image and save it to *output_dir*."""
    if not os.path.exists(card['art_file']):
        raise FileNotFoundError(card['art_file'])

    art = Image.open(card['art_file']).convert('RGBA')

    # Draw the trimmed area first and then place it on a larger canvas
    trimmed = Image.new('RGBA', (TRIM_WIDTH, TRIM_HEIGHT), 'white')
    draw = ImageDraw.Draw(trimmed)

    title_font = load_font(TITLE_FONT, 40)
    text_font = load_font(TEXT_FONT, 24)

    border_color = COLOR_MAP.get(card['color'].lower(), 'white')
    draw.rectangle(
        [0, 0, TRIM_WIDTH - 1, TRIM_HEIGHT - 1],
        outline=border_color,
        width=12,
    )

    draw.rectangle([20, 20, TRIM_WIDTH-20, 90], fill=border_color)
    draw.text((30, 30), card['name'], font=title_font, fill='black')
    draw.text(
        (TRIM_WIDTH - 150, 30),
        card['cost'],
        font=title_font,
        fill='black',
    )

    art_area_height = 520
    art_target_width = TRIM_WIDTH - 40
    art_target_height = art_area_height
    ratio = min(art_target_width / art.width, art_target_height / art.height)
    resized = art.resize((int(art.width*ratio), int(art.height*ratio)))
    art_x = (TRIM_WIDTH - resized.width) // 2
    art_y = 110 + (art_target_height - resized.height)//2
    trimmed.paste(resized, (art_x, art_y))

    text_y = 110 + art_area_height + 20
    text_box = [20, text_y, TRIM_WIDTH-20, TRIM_HEIGHT-110]
    draw.rectangle(text_box, fill='white')
    if card['type'].lower() == 'creature':
        desc = f"Strength: {card['strength']}"
    else:
        desc = card['description']
    draw.multiline_text((30, text_y+10), desc, font=text_font, fill='black')

    # Place trimmed artwork on a larger canvas for bleed
    card_img = Image.new('CMYK', (CARD_WIDTH, CARD_HEIGHT), 'white')
    card_img.paste(trimmed.convert('CMYK'), (BLEED, BLEED))

    out_name = f"{card['name'].replace(' ', '_')}.jpg"
    out_path = os.path.join(output_dir, out_name)
    card_img.save(out_path, 'JPEG', dpi=(DPI, DPI))
    print('Saved', out_path)


def main(csv_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            draw_card(row, output_dir)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('Usage: python generate_cards.py <cards.csv> <output_dir>')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
