import functools
import os, os.path
import warnings

import libimagequant as liq

# PIL internally raises some DeprecationWarnings upon import -- block
# those so they don't affect our actual tests
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    import PIL.Image

import pytest


########################################################################
########################### Helper Functions ###########################
########################################################################

@functools.lru_cache()
def load_test_image(name):
    """
    Load the test image with the given name.
    Return a triple (width, height, pixeldata), where pixeldata is
    a bytes object with RGBA data.
    """
    img = PIL.Image.open(os.path.join(os.path.dirname(__file__), 'res', name)).convert('RGBA')
    width = img.width
    height = img.height
    pixeldata = img.tobytes()

    return width, height, pixeldata


def try_multiple_values(img, values, *,
        attr_callback=None, image_callback=None, result_callback=None,
        allow_exceptions=False):
    """
    Helper function that lets you easily perform multiple quantizations
    and ensure that all of the outputs are different.
    Use attr_callback(value, attr) to modify the Attr object, and use
    result_callback(value, result) to modify the Result object.
    """
    width, height, input_pixels = load_test_image(img)

    tuples = []
    for value in values:
        attr = input_image = result = exception = None

        try:
            attr = liq.Attr()
            if attr_callback is not None:
                attr_callback(value, attr)

            input_image = attr.create_rgba(input_pixels, width, height, 0)
            if image_callback is not None:
                image_callback(value, input_image)

            result = input_image.quantize(attr)
            if result_callback is not None:
                result_callback(value, result)

        except Exception as e:
            if allow_exceptions:
                exception = e
            else:
                raise

        tuples.append((attr, input_image, result, exception))

    return tuples


def get_output_datas(tuples):
    L = []
    for a, ii, r, e in tuples:
        if r is None:
            L.append(None)
        else:
            L.append(r.remap_image(ii))
    return L


def check_outputs_unique(output_datas):
    assert len(output_datas) == len(set(output_datas))


def make_Image(input_image, result):
    """
    Debug function for creating a PIL.Image
    """
    raw_8bit_pixels = result.remap_image(input_image)
    palette = result.get_palette()

    img = PIL.Image.frombytes('P', (input_image.width, input_image.height), bytes(raw_8bit_pixels))

    paletteData = []
    for ent in palette:
        paletteData.append(ent.r)
        paletteData.append(ent.g)
        paletteData.append(ent.b)
    img.putpalette(paletteData)

    img = img.convert('RGBA')
    return img


########################################################################
################################# Tests ################################
########################################################################

# ----------------------------------------------------------------------
# -------------------------------- Meta --------------------------------
# ----------------------------------------------------------------------


def test_version_info():
    """
    Test that the library version constants exist and seem sane
    """
    assert isinstance(liq.LIQ_VERSION, int)
    assert isinstance(liq.LIQ_VERSION_STRING, str)
    assert isinstance(liq.BINDINGS_VERSION, int)
    assert isinstance(liq.BINDINGS_VERSION_STRING, str)

    # Check that the version strings match the version ints

    def version_int_to_string(value):
        parts = []
        while value:
            parts.insert(0, str(value % 100))
            value //= 100
        return '.'.join(parts)

    assert liq.LIQ_VERSION_STRING == version_int_to_string(liq.LIQ_VERSION)
    assert liq.BINDINGS_VERSION_STRING == version_int_to_string(liq.BINDINGS_VERSION)


# ----------------------------------------------------------------------
# -------------------------------- Attr --------------------------------
# ----------------------------------------------------------------------


def test_attr_copy():
    """
    Test Attr.copy()
    """
    width, height, input_pixels = load_test_image('flower.jpg')

    attr = liq.Attr()
    attr.max_colors = 88
    attr.min_posterization = 3
    attr.min_quality = 55

    attr2 = attr.copy()
    assert attr2.max_colors == 88
    assert attr2.min_posterization == 3
    assert attr2.min_quality == 55


def test_attr_max_colors():
    """
    Test Attr.max_colors
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.max_colors = value
        assert attr.max_colors == value

        # Test bounds checking (2-256)
        with pytest.raises(ValueError):
            attr.max_colors = 1
        with pytest.raises(ValueError):
            attr.max_colors = 257

    (_, _, result, _), = try_multiple_values(
        'flower.jpg',
        [77],
        attr_callback=attr_callback)
    assert len(result.get_palette()) == 77


def test_attr_speed():
    """
    Test Attr.speed
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.speed = value
        assert attr.speed == value

        # Test bounds checking (1-10)
        with pytest.raises(ValueError):
            attr.speed = 0
        with pytest.raises(ValueError):
            attr.speed = 11

    check_outputs_unique(get_output_datas(try_multiple_values(
        'flower.jpg',
        [1, 5, 10],
        attr_callback=attr_callback)))


def test_attr_min_opacity():
    """
    Test Attr.min_opacity
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.min_opacity = value
        assert attr.min_opacity == value

        # Test bounds checking (0-255)
        with pytest.raises(ValueError):
            attr.min_opacity = -1
        with pytest.raises(ValueError):
            attr.min_opacity = 256

    check_outputs_unique(get_output_datas(try_multiple_values(
        'alpha-gradient.png',
        [0, 63, 127, 191, 255],
        attr_callback=attr_callback)))


def test_attr_min_posterization():
    """
    Test Attr.min_posterization
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.min_posterization = value
        assert attr.min_posterization == value

        # Test bounds checking (0-4)
        with pytest.raises(ValueError):
            attr.min_posterization = -1
        with pytest.raises(ValueError):
            attr.min_posterization = 5

    check_outputs_unique(get_output_datas(try_multiple_values(
        'flower.jpg',
        [0, 1, 2, 3, 4],
        attr_callback=attr_callback)))


def test_attr_min_quality():
    """
    Test Attr.min_quality
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.min_quality = value
        assert attr.min_quality == value

        # Test bounds checking (0-100)
        with pytest.raises(ValueError):
            attr.min_quality = -1
        with pytest.raises(ValueError):
            attr.min_quality = 101

    tuples = try_multiple_values(
        'flower.jpg',
        [0, 25, 75, 90, 100],
        attr_callback=attr_callback,
        allow_exceptions=True)

    actual_exceptions = [e for (a, ii, r, e) in tuples]
    
    NoneType = type(None)
    expected_exceptions = [NoneType, NoneType, NoneType, liq.QualityTooLowError, liq.QualityTooLowError]

    assert all(isinstance(a, b) for a, b in zip(actual_exceptions, expected_exceptions))


def test_attr_max_quality():
    """
    Test Attr.max_quality
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.max_quality = value
        assert attr.max_quality == value

        # Test bounds checking (0-100)
        with pytest.raises(ValueError):
            attr.max_quality = -1
        with pytest.raises(ValueError):
            attr.max_quality = 101

    check_outputs_unique(get_output_datas(try_multiple_values(
        'flower.jpg',
        [0, 33, 66, 100],
        attr_callback=attr_callback)))


def test_attr_last_index_transparent():
    """
    Test Attr.last_index_transparent
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.last_index_transparent = value
        with pytest.raises(AttributeError):
            attr.last_index_transparent

    tuples = try_multiple_values(
        'alpha-gradient.png',
        [False, True],
        attr_callback=attr_callback)
    palettes = [r.get_palette() for (a, ii, r, e) in tuples]

    # palettes[0] (last_index_transparent=False): alpha colors at beginning
    assert palettes[0][0].a == 0
    assert palettes[0][-1].a == 255

    # palettes[1] (last_index_transparent=True): alpha colors at end
    assert palettes[1][0].a == 255
    assert palettes[1][-1].a == 0


def test_attr_set_log_callback():
    """
    Test Attr.set_log_callback()
    """
    my_attr = None
    my_user_info = object()

    callback_attrs = []
    callback_messages = []
    callback_user_infos = []

    def log_callback(attr, message, user_info):
        # Assertions get eaten if performed in the callback, so let's put
        # these objects into lists we can check later
        callback_attrs.append(attr)
        callback_messages.append(message)
        callback_user_infos.append(user_info)

        print(message)

    def attr_callback(value, attr):
        """
        Set the log callback.
        Also grab a reference to the Attr object so we can later check
        that the one passed to the log callback matches
        """
        nonlocal my_attr
        my_attr = attr
        attr.set_log_callback(log_callback, my_user_info)

        # Try clearing the callback (to test that code path)
        attr.set_log_callback(None, None)

        # (set it back properly again)
        attr.set_log_callback(log_callback, my_user_info)

    try_multiple_values(
        'flower.jpg',
        [None],
        attr_callback=attr_callback)

    # Check that we got a good amount of callback items
    assert len(callback_attrs) == len(callback_messages) == len(callback_user_infos) > 0

    # Check that the log callback arguments were correct
    assert all(attr is my_attr for attr in callback_attrs)
    assert all(ui is my_user_info for ui in callback_user_infos)

    # Check the callback messages
    for m in callback_messages:
        assert isinstance(m, str) and len(m) >= 20


def test_attr_set_progress_callback():
    """
    Test Attr.set_progress_callback()
    """
    my_attr = None
    my_user_info = object()

    callback_percentages = []
    callback_user_infos = []

    def progress_callback(progress_percent, user_info):
        # Assertions get eaten if performed in the callback, so let's put
        # these objects into lists we can check later
        callback_percentages.append(progress_percent)
        callback_user_infos.append(user_info)

        print(progress_percent)

        return True # returning False to abort is a separate test

    def attr_callback(value, attr):
        """
        Set the progress callback.
        Also grab a reference to the Attr object so we can later check
        that the one passed to the progress callback matches.
        """
        nonlocal my_attr
        my_attr = attr
        attr.set_progress_callback(progress_callback, my_user_info)

        # Try clearing the callback (to test that code path)
        attr.set_progress_callback(None, None)

        # (set it back properly again)
        attr.set_progress_callback(progress_callback, my_user_info)

    try_multiple_values(
        'flower.jpg',
        [None],
        attr_callback=attr_callback)

    # Check that we got a good amount of callback items
    assert len(callback_percentages) == len(callback_user_infos) > 0

    # Check that the user infos were correct
    assert all(ui is my_user_info for ui in callback_user_infos)

    # Check that the progress percentages are in the 0.0-100.0 range
    assert all(0 <= pct <= 100 for pct in callback_percentages)


def test_attr_set_progress_callback_abort():
    """
    Test aborting from Attr.set_progress_callback()
    """

    def progress_callback(progress_percent, user_info):
        """
        Progress callback that just returns False, which should abort
        the operation and cause a liq.AbortedError
        """
        return False

    def attr_callback(value, attr):
        """
        Set the progress callback
        """
        attr.set_progress_callback(progress_callback, None)

    with pytest.raises(liq.AbortedError):
        try_multiple_values(
            'flower.jpg',
            [None],
            attr_callback=attr_callback)


# There's not much to test for create_rgba(), especially considering
# that we use it as part of most of the other tests. So let's skip it.


# ----------------------------------------------------------------------
# ------------------------------- Image --------------------------------
# ----------------------------------------------------------------------


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
        width, height, input_pixels = load_test_image(value)
        attr = liq.Attr()
        background = attr.create_rgba(input_pixels, width, height, 0)
        backgrounds.append(background)

        # Test both the getter and setter methods
        image.background = background
        with pytest.raises(AttributeError):
            image.background

    check_outputs_unique(get_output_datas(try_multiple_values(
        'alpha-gradient.png',
        ['test-card_480_360.png'], # ['flower.jpg', 'test-card_480_360.png'],
        image_callback=image_callback)))


def test_image_importance_map():
    """
    Test Image.importance_map
    """

    def image_callback(value, image):

        # Load the map as a bytearray
        width, height, input_pixels = load_test_image(value)
        buffer = bytearray(width * height)
        for i in range(0, len(input_pixels), 4):
            buffer[i // 4] = input_pixels[i]

        # Test both the getter and setter methods
        image.importance_map = buffer
        with pytest.raises(AttributeError):
            image.importance_map

    check_outputs_unique(get_output_datas(try_multiple_values(
        'alpha-gradient.png',
        ['importance-map-1.png', 'importance-map-2.png', 'importance-map-3.png'],
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

    tuples = try_multiple_values(
        'flower.jpg',
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

    # flower.jpg (480x360)
    # --------------------

    def image_callback_1(value, image):
        assert image.width == 480
        assert image.height == 360

        with pytest.raises(AttributeError):
            image.width = 256
        with pytest.raises(AttributeError):
            image.height = 256

    try_multiple_values(
        'flower.jpg',
        [None],
        image_callback=image_callback_1)

    # test-card.png (640x480)
    # -----------------------

    def image_callback_2(value, image):
        assert image.width == 640
        assert image.height == 480

        with pytest.raises(AttributeError):
            image.width = 256
        with pytest.raises(AttributeError):
            image.height = 256

    try_multiple_values(
        'test-card.png',
        [None],
        image_callback=image_callback_2)


# There's not much to test for quantize(), especially considering that
# we use it as part of most of the other tests. So let's skip it.


# ----------------------------------------------------------------------
# ------------------------------- Result -------------------------------
# ----------------------------------------------------------------------


def test_result_constructor():
    """
    Test creating a Result directly (should fail)
    """
    with pytest.raises(RuntimeError):
        liq.Result()


def test_result_set_progress_callback():
    """
    Test Result.set_progress_callback()
    """
    my_result = None
    my_user_info = object()

    callback_percentages = []
    callback_user_infos = []

    def progress_callback(progress_percent, user_info):
        # Assertions get eaten if performed in the callback, so let's put
        # these objects into lists we can check later
        callback_percentages.append(progress_percent)
        callback_user_infos.append(user_info)

        print(progress_percent)

        return True # returning False to abort is a separate test

    def attr_callback(value, attr):
        """
        Encourage dithering by setting a strict max_colors value
        """
        attr.max_colors = 10

    def result_callback(value, result):
        """
        Enable dithering and set the progress callback.
        Also grab a reference to the Result object so we can later check
        that the one passed to the progress callback matches.
        """
        nonlocal my_result
        my_result = result

        # Encourage dithering by setting a high dithering level
        result.dithering_level = 1.0

        # Set the progress callback
        result.set_progress_callback(progress_callback, my_user_info)

        # Try clearing the callback (to test that code path)
        result.set_progress_callback(None, None)

        # (set it back properly again)
        result.set_progress_callback(progress_callback, my_user_info)

    tuples = try_multiple_values(
        'flower.jpg',
        [None],
        attr_callback=attr_callback,
        result_callback=result_callback)

    # We need to call remap_image() on the Result to trigger the
    # progress callbacks
    for a, ii, r, e in tuples:
        r.remap_image(ii)

    # Check that we got a good amount of callback items
    assert len(callback_percentages) == len(callback_user_infos) > 0

    # Check that the user infos were correct
    assert all(ui is my_user_info for ui in callback_user_infos)

    # Check that the progress percentages are in the 0.0-100.0 range
    assert all(0 <= pct <= 100 for pct in callback_percentages)


def test_result_set_progress_callback_abort():
    """
    Test aborting from Result.set_progress_callback()
    """

    def progress_callback(progress_percent, user_info):
        """
        Progress callback that just returns False, which should abort
        the operation and cause a liq.AbortedError
        """
        return False

    def attr_callback(value, attr):
        """
        Encourage dithering by setting a strict max_colors value
        """
        attr.max_colors = 10

    def result_callback(value, result):
        """
        Enable dithering and set the progress callback
        """
        # Encourage dithering by setting a high dithering level
        result.dithering_level = 1.0

        result.set_progress_callback(progress_callback, None)

    tuples = try_multiple_values(
        'flower.jpg',
        [None],
        attr_callback=attr_callback,
        result_callback=result_callback)

    # We need to call remap_image() on the Result to trigger the
    # progress callbacks
    with pytest.raises(liq.AbortedError):
        for a, ii, r, e in tuples:
            r.remap_image(ii)


@pytest.mark.xfail(liq.LIQ_VERSION <= 21205,
                   reason='dithering_level bounds-checking bug in LIQ 2.12.5 and older')
def test_result_dithering_level():
    """
    Test Result.dithering_level
    """

    def result_callback(value, result):
        # Test the setter, and ensure the getter raises AttributeError
        result.dithering_level = value
        with pytest.raises(AttributeError):
            result.dithering_level

        # Test bounds checking (0.0-1.0)
        with pytest.raises(ValueError):
            result.dithering_level = -0.1
        with pytest.raises(ValueError):
            result.dithering_level = 1.1

    check_outputs_unique(get_output_datas(try_multiple_values(
        'flower.jpg',
        [0.0, 0.5, 1.0],
        result_callback=result_callback)))


def test_result_output_gamma():
    """
    Test Result.output_gamma
    """

    def result_callback(value, result):
        # Test the setter, and ensure the getter raises AttributeError
        result.output_gamma = value
        assert result.output_gamma == value

        # Test bounds checking (0.0-1.0, not inclusive)
        with pytest.raises(ValueError):
            result.output_gamma = -0.1
        with pytest.raises(ValueError):
            result.output_gamma = 0.0
        with pytest.raises(ValueError):
            result.output_gamma = 1.0
        with pytest.raises(ValueError):
            result.output_gamma = 1.1

    check_outputs_unique(get_output_datas(try_multiple_values(
        'flower.jpg',
        [0.01, 0.5, 0.99],
        result_callback=result_callback)))


def test_result_get_palette():
    """
    Test Result.get_palette()
    """

    (_, _, result, _), = try_multiple_values(
        'flower.jpg',
        [None])

    palette = result.get_palette()

    assert palette
    assert all(isinstance(col, liq.Color) for col in palette)


# There's not much to test for remap_image(), especially considering
# that we use it as part of most of the other tests. So let's skip it.


def test_result_quantization_and_remapping_error_and_quality():
    """
    Test:
        - Result.quantization_error
        - Result.quantization_quality
        - Result.remapping_error
        - Result.remapping_quality
    """

    (_, image, result, _), = try_multiple_values(
        'flower.jpg',
        [None])

    # Not sure what the actual maxes for quantization_error and remapping_error are
    assert 0 < result.quantization_error < 255
    assert 0 < result.quantization_quality < 100

    # Remapping error and quality aren't available until after remapping
    assert result.remapping_error == -1.0
    assert result.remapping_quality == -1.0

    result.remap_image(image)

    # *Now* they're available
    assert 0 < result.remapping_error < 255
    assert 0 < result.remapping_quality < 100


# ----------------------------------------------------------------------
# ----------------------------- Histogram ------------------------------
# ----------------------------------------------------------------------


def test_histogram_basic():
    """
    Basic test of Histogram:
    - __init__()
    - add_image()
    - quantize()
    """
    # Testing with three input images
    width_A, height_A, input_pixels_A = load_test_image('flower.jpg')
    width_B, height_B, input_pixels_B = load_test_image('flower-huechange-1.jpg')
    width_C, height_C, input_pixels_C = load_test_image('flower-huechange-2.jpg')
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
    width, height, input_pixels = load_test_image('flower-huechange-1.jpg')
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
    width, height, input_pixels = load_test_image('flower.jpg')
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
    width_A, height_A, input_pixels_A = load_test_image('flower.jpg')
    width_B, height_B, input_pixels_B = load_test_image('flower-huechange-1.jpg')
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


# ----------------------------------------------------------------------
# ----------------------------- Exceptions -----------------------------
# ----------------------------------------------------------------------


def test_quality_too_low_error():
    """
    Trigger LIQ_QUALITY_TOO_LOW and ensure that liq.QualityTooLowError
    is raised
    """

    def attr_callback(value, attr):
        attr.max_colors = 10
        attr.min_quality = 99

    with pytest.raises(liq.QualityTooLowError):
        get_output_datas(try_multiple_values(
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
    width, height, input_pixels = load_test_image('test-card.png')
    attr = liq.Attr()
    background = attr.create_rgba(input_pixels, width, height, 0)

    def image_callback(value, image):
        # The image is too large, so using it as a background should fail
        with pytest.raises(liq.BufferTooSmallError):
            image.background = background

    try_multiple_values(
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
