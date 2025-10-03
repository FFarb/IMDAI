from PIL import Image

from discovery.features import estimate_brand_risk


def test_estimate_brand_risk_flags_brand_tokens() -> None:
    blank = Image.new('RGB', (64, 64), color='white')
    metadata = {'title': 'Disney castle concept', 'author': 'unknown', 'license': 'CC', 'url': 'https://example.com'}
    risk = estimate_brand_risk(blank, metadata)
    assert risk > 0.6


def test_estimate_brand_risk_low_for_generic() -> None:
    blank = Image.new('RGB', (64, 64), color='white')
    metadata = {'title': 'soft pastel landscape', 'author': 'artist', 'license': 'CC', 'url': 'https://example.com'}
    risk = estimate_brand_risk(blank, metadata)
    assert risk < 0.4
