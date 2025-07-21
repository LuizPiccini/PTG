# Card Generator

This repository contains a small tool for generating printable card images from
a CSV file using Pillow. Card frames and fonts must be supplied separately (see
`assets/README.md`).

## Requirements

- Python 3
- [Pillow](https://python-pillow.org/) (`pip install Pillow`)

## Usage

Prepare a CSV file with the following columns:

```
name,cost,type,subtype,color,art_file,strength,description
```

- **name**: Card name
- **cost**: Mana or resource cost (e.g., `{2}{R}`)
- **type**: `Creature` or `Spell`
- **subtype**: Subtype or rules text header
- **color**: Card colour; determines which frame is used
- **art_file**: Optional path to artwork image. If omitted, the script will
  look for `art/<slugified name>.png`.
- **strength**: Strength value for creatures
- **description**: Rules text for spells

Run the generator:

```
python3 generate_cards.py cards.csv output_cards
```

Generated TIFF images suitable for printing will be placed in `output_cards/`.
The output files are CMYK TIFF images at 300 DPI sized 63×88 mm (no bleed).
