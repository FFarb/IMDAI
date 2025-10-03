from PIL import Image, ImageDraw, ImageChops

from discovery.features import measure_outline


def _make_line_image(width: int) -> Image.Image:
    image = Image.new('L', (128, 128), color=255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 108, 108), outline=0, width=width)
    return image.convert('RGB')


def test_measure_outline_distinguishes_line_weight() -> None:
    thin = _make_line_image(1)
    bold = _make_line_image(8)

    thin_weight, _ = measure_outline(thin)
    bold_weight, _ = measure_outline(bold)

    assert bold_weight > thin_weight


def test_measure_outline_rewards_clarity() -> None:
    clean = _make_line_image(4)
    noisy_base = _make_line_image(4)
    noise = Image.effect_noise((128, 128), 64).convert('L')
    noisy = ImageChops.add(noisy_base.convert('L'), noise, scale=2.0).convert('RGB')

    _, clean_clarity = measure_outline(clean)
    _, noisy_clarity = measure_outline(noisy)

    assert clean_clarity > noisy_clarity
