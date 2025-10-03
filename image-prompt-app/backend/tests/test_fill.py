from PIL import Image, ImageDraw

from discovery.features import measure_fill_ratio


def test_measure_fill_ratio_orders_by_coverage() -> None:
    dense = Image.new('L', (128, 128), color=255)
    draw_dense = ImageDraw.Draw(dense)
    draw_dense.rectangle((16, 16, 112, 112), fill=0)

    sparse = Image.new('L', (128, 128), color=255)
    draw_sparse = ImageDraw.Draw(sparse)
    draw_sparse.rectangle((48, 48, 80, 80), fill=0)

    dense_ratio = measure_fill_ratio(dense.convert('RGB'))
    sparse_ratio = measure_fill_ratio(sparse.convert('RGB'))

    assert dense_ratio > sparse_ratio
    assert 0.0 <= dense_ratio <= 1.0
