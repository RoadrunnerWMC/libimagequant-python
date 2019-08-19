import libimagequant as liq
import pytest

import utils


def test_quality_too_low_error():
    """
    Trigger LIQ_QUALITY_TOO_LOW and ensure that liq.QualityTooLowError
    is raised
    """

    def attr_callback(value, attr):
        attr.max_colors = 10
        attr.min_quality = 99

    with pytest.raises(liq.QualityTooLowError):
        utils.get_output_datas(utils.try_multiple_values(
            'flower.jpg',
            [None],
            attr_callback=attr_callback))


# Other tests test for LIQ_VALUE_OUT_OF_RANGE already, so, skip

# There probably isn't a portable way of reliably triggering
# LIQ_OUT_OF_MEMORY, so, skip

# Other tests test for LIQ_ABORTED already, so, skip


def test_bitmap_not_available_error():
    """
    Trigger LIQ_BITMAP_NOT_AVAILABLE and ensure that
    liq.BitmapNotAvailableError is raised
    """

    attr = liq.Attr()
    hist = liq.Histogram(attr)

    with pytest.raises(liq.BitmapNotAvailableError):
        result = hist.quantize(attr)


def test_buffer_too_small_error():
    """
    Trigger LIQ_BUFFER_TOO_SMALL and ensure that liq.BufferTooSmallError
    is raised
    """

    # Load the background as an Image
    width, height, input_pixels = utils.load_test_image('test-card.png')
    attr = liq.Attr()
    background = attr.create_rgba(input_pixels, width, height, 0)

    def image_callback(value, image):
        # The image is too large, so using it as a background should fail
        with pytest.raises(liq.BufferTooSmallError):
            image.background = background

    utils.try_multiple_values(
        'alpha-gradient.png',
        [None],
        image_callback=image_callback)


# We can't test for LIQ_INVALID_POINTER without doing some ridiculously
# hacky and unsupported things, so let's not.


def test_unsupported_error():
    """
    Trigger LIQ_UNSUPPORTED and ensure that liq.UnsupportedError is
    raised
    """

    # A simple way of getting LIQ_UNSUPPORTED is adding more than 256
    # fixed colors to a histogram

    attr = liq.Attr()
    hist = liq.Histogram(attr)

    for i in range(256):
        hist.add_fixed_color(liq.Color(i, 0, 0, 255), 0)

    with pytest.raises(liq.UnsupportedError):
        hist.add_fixed_color(liq.Color(255, 255, 0, 255), 0)
