import libimagequant as liq
import pytest

import utils


def test_image_constructor():
    """
    Test creating an Image directly (should fail)
    """
    with pytest.raises(RuntimeError):
        liq.Image()


def test_image_background():
    """
    Test Image.background
    """
    backgrounds = []

    def image_callback(value, image):

        # Load the background as an Image
        width, height, input_pixels = utils.load_test_image(value)
        attr = liq.Attr()
        background = attr.create_rgba(input_pixels, width, height, 0)
        backgrounds.append(background)

        # Test both the getter and setter methods
        image.background = background
        with pytest.raises(AttributeError):
            image.background

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'alpha-gradient',
        ['test-card_480_360'], # ['flower', 'test-card_480_360'],
        image_callback=image_callback)))


def test_image_importance_map():
    """
    Test Image.importance_map
    """

    def image_callback(value, image):

        # Load the map as a bytearray
        width, height, input_pixels = utils.load_test_image(value)
        buffer = bytearray(width * height)
        for i in range(0, len(input_pixels), 4):
            buffer[i // 4] = input_pixels[i]

        # Test both the getter and setter methods
        image.importance_map = buffer
        with pytest.raises(AttributeError):
            image.importance_map

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'alpha-gradient',
        ['importance-map-1', 'importance-map-2', 'importance-map-3'],
        image_callback=image_callback)))


def test_image_add_fixed_color():
    """
    Test Image.add_fixed_color()
    """

    def image_callback(value, image):

        for fixedColor in value:
            image.add_fixed_color(fixedColor)

    FIXED_COLORS = [
        [liq.Color(255, 0, 0, 255)], # red
        [liq.Color(0, 0, 255, 255)], # blue
        [liq.Color(128, 0, 128, 255), liq.Color(255, 255, 0, 255)], # purple & yellow
    ]

    tuples = utils.try_multiple_values(
        'flower',
        FIXED_COLORS,
        image_callback=image_callback)
    palettes = [r.get_palette() for (a, ii, r, e) in tuples]

    for fixedColors, pal in zip(FIXED_COLORS, palettes):
        for fixedColor in fixedColors:
            assert fixedColor in pal


def test_image_width_height():
    """
    Test Image.width and Image.height
    """

    # flower (480x360)
    # ----------------

    def image_callback_1(value, image):
        assert image.width == 480
        assert image.height == 360

        with pytest.raises(AttributeError):
            image.width = 256
        with pytest.raises(AttributeError):
            image.height = 256

    utils.try_multiple_values(
        'flower',
        [None],
        image_callback=image_callback_1)

    # test-card (640x480)
    # -------------------

    def image_callback_2(value, image):
        assert image.width == 640
        assert image.height == 480

        with pytest.raises(AttributeError):
            image.width = 256
        with pytest.raises(AttributeError):
            image.height = 256

    utils.try_multiple_values(
        'test-card',
        [None],
        image_callback=image_callback_2)


# There's not much to test for quantize(), especially considering that
# we use it as part of most of the other tests. So let's skip it.
