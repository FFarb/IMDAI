from PIL import Image

from discovery.features import extract_palette


def test_extract_palette_returns_weighted_hexes() -> None:
    image = Image.new('RGB', (90, 90), '#FFAA00')
    for y in range(45):
        for x in range(90):
            image.putpixel((x, y), (50, 120, 220))
    for y in range(90):
        for x in range(30):
            image.putpixel((x, y), (200, 80, 160))

    palette = extract_palette(image)

    assert 5 <= len(palette) <= 7
    total_weight = sum(color.weight for color in palette)
    assert abs(total_weight - 1.0) < 1e-6
    for entry in palette:
        assert entry.hex.startswith('#')
