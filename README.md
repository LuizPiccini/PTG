# Card Generator

This repository contains a small tool for generating printable card images from a CSV file.

## Requirements

- Python 3
- [Pillow](https://python-pillow.org/) (`pip install Pillow`)

## Usage

Prepare a CSV file with the following columns:

```
name,cost,type,color,art_file,strength,description
```

- **name**: Card name
- **cost**: Mana or resource cost (e.g., `2W`)
- **type**: `creature` or `spell`
- **color**: `white`, `blue`, `black`, `red`, or `green`
- **art_file**: Path to the artwork image
- **strength**: Strength value for creatures
- **description**: Text description for spells

Run the generator:

```
python3 generate_cards.py cards.csv output_cards
```

Generated PNG images will be placed in `output_cards/`.
