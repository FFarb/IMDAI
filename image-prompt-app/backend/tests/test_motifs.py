from PIL import Image, ImageDraw

from discovery.features import detect_motifs


def _star_image() -> Image.Image:
    image = Image.new('RGB', (160, 160), 'white')
    draw = ImageDraw.Draw(image)
    points = [
        (80, 20),
        (98, 64),
        (144, 64),
        (108, 94),
        (124, 140),
        (80, 114),
        (36, 140),
        (52, 94),
        (16, 64),
        (62, 64),
    ]
    draw.polygon(points, fill=(250, 215, 0))
    return image


def _cloud_image() -> Image.Image:
    image = Image.new('RGB', (160, 160), (180, 220, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((30, 70, 90, 120), fill='white')
    draw.ellipse((60, 60, 120, 120), fill='white')
    draw.ellipse((90, 70, 150, 120), fill='white')
    draw.rectangle((40, 95, 140, 120), fill='white')
    return image


def test_detect_motifs_identifies_shapes() -> None:
    star_tags = detect_motifs(_star_image())
    cloud_tags = detect_motifs(_cloud_image())

    assert 'stars' in star_tags
    assert 'clouds' in cloud_tags
    assert len(star_tags) >= 8
    assert len(cloud_tags) >= 8
    for tags in (star_tags, cloud_tags):
        assert all('logo' not in tag for tag in tags)
