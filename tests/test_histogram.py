import libimagequant as liq
import pytest

import utils


def test_histogram_basic():
    """
    Basic test of Histogram:
    - __init__()
    - add_image()
    - quantize()
    """
    # Testing with three input images
    width_A, height_A, input_pixels_A = utils.load_test_image('flower.jpg')
    width_B, height_B, input_pixels_B = utils.load_test_image('flower-huechange-1.jpg')
    width_C, height_C, input_pixels_C = utils.load_test_image('flower-huechange-2.jpg')
    assert width_A == width_B == width_C
    assert height_A == height_B == height_C
    width, height = width_A, height_A

    attr = liq.Attr()
    hist = liq.Histogram(attr)

    image_A = attr.create_rgba(input_pixels_A, width, height, 0)
    hist.add_image(attr, image_A)

    image_B = attr.create_rgba(input_pixels_B, width, height, 0)
    hist.add_image(attr, image_B)

    image_C = attr.create_rgba(input_pixels_C, width, height, 0)
    hist.add_image(attr, image_C)

    result = hist.quantize(attr)

    # Check that we have a decently-sized palette
    assert len(result.get_palette()) > 128

    # Try remapping all three images -- make sure we don't get an
    # exception or something
    result.remap_image(image_A)
    result.remap_image(image_B)
    result.remap_image(image_C)


def test_histogram_add_colors():
    """
    Test Histogram.add_colors(), as well as the HistogramEntry class
    """

    # First, quantize flower-huechange-1.jpg on its own
    width, height, input_pixels = utils.load_test_image('flower-huechange-1.jpg')
    attr = liq.Attr()
    other_image = attr.create_rgba(input_pixels, width, height, 0)
    result = other_image.quantize(attr)
    result_pixels = result.remap_image(other_image)
    result_palette = result.get_palette()

    # ~

    # Create a list of HistogramEntrys for it
    entries = []
    for i, color in enumerate(result_palette):
        count = result_pixels.count(i)

        entry = liq.HistogramEntry(color, count)
        entries.append(entry)

        # Test HistogramEntry getters
        assert entry.color == color
        assert entry.count == count

        # Test setters
        entry.color = result_palette[0]
        entry.count = 50
        assert entry.color == result_palette[0]
        assert entry.count == 50

        # (Set properties back to what they should be)
        entry.color = color
        entry.count = count

    assert entries

    # ~

    # Set up a Histogram
    attr = liq.Attr()
    hist = liq.Histogram(attr)

    # Add flower.jpg as an image
    width, height, input_pixels = utils.load_test_image('flower.jpg')
    image = attr.create_rgba(input_pixels, width, height, 0)
    hist.add_image(attr, image)

    # Add the HistogramEntrys for flower-huechange-1.jpg
    hist.add_colors(attr, entries, 0)

    # And quantize
    result = hist.quantize(attr)

    # ~

    # Check that we have a decently-sized palette
    assert len(result.get_palette()) > 128

    # Try remapping both images -- make sure we don't get an exception
    # or something
    result.remap_image(image)
    result.remap_image(other_image)


def test_histogram_add_fixed_color():
    """
    Test Histogram.add_fixed_color
    """
    width_A, height_A, input_pixels_A = utils.load_test_image('flower.jpg')
    width_B, height_B, input_pixels_B = utils.load_test_image('flower-huechange-1.jpg')
    assert width_A == width_B
    width, height = width_A, height_A

    attr = liq.Attr()
    hist = liq.Histogram(attr)

    image_A = attr.create_rgba(input_pixels_A, width, height, 0)
    hist.add_image(attr, image_A)

    image_B = attr.create_rgba(input_pixels_B, width, height, 0)
    hist.add_image(attr, image_B)

    FIXED_COLORS = [
        liq.Color(255, 0, 0, 255), # red
        liq.Color(0, 0, 255, 255), # blue
        liq.Color(128, 0, 128, 255), # purple
        liq.Color(255, 255, 0, 255), # yellow
    ]

    for fixedColor in FIXED_COLORS:
        hist.add_fixed_color(fixedColor, 0)

    result = hist.quantize(attr)
    result_palette = result.get_palette()

    # Check that we have a decently-sized palette
    assert len(result_palette) > 128

    # Try remapping both images -- make sure we don't get an exception
    # or something
    result.remap_image(image_A)
    result.remap_image(image_B)

    # Check that the fixed colors are present in the output palette
    for fixedColor in FIXED_COLORS:
        assert fixedColor in result_palette
