from PIL import Image, ImageDraw, ImageFont

from discovery.features import detect_typography


def test_detect_typography_identifies_text() -> None:
    font = ImageFont.load_default()
    text_image = Image.new('RGB', (200, 120), color='white')
    draw = ImageDraw.Draw(text_image)
    draw.text((10, 40), 'HELLO', fill='black', font=font)

    result = detect_typography(text_image)
    assert result.present is True


def test_detect_typography_absence() -> None:
    blank = Image.new('RGB', (200, 120), color='white')
    result = detect_typography(blank)
    assert result.present is False
