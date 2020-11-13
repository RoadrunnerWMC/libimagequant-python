import libimagequant as liq
import pytest

import utils


def test_attr_copy():
    """
    Test Attr.copy()
    """
    width, height, input_pixels = utils.load_test_image('flower')

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

    (_, _, result, _), = utils.try_multiple_values(
        'flower',
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

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'flower',
        [1, 5, 10],
        attr_callback=attr_callback)))


@pytest.mark.skipif(liq.LIQ_VERSION >= 21300, reason='min_opacity was replaced with a stub in liq 2.13.0')
def test_attr_min_opacity():
    """
    Test Attr.min_opacity (original implementation, < liq 2.13.0)
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

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'alpha-gradient',
        [0, 63, 127, 191, 255],
        attr_callback=attr_callback)))


@pytest.mark.skipif(liq.LIQ_VERSION < 21300, reason='min_opacity had a real implementation before liq 2.13.0')
def test_attr_min_opacity_stub():
    """
    Test Attr.min_opacity (stub implementation, >= liq 2.13.0)
    """

    def attr_callback(value, attr):
        # Test both the getter and setter methods
        attr.min_opacity = value
        assert attr.min_opacity == 0

        # There shouldn't be any bounds checking anymore
        attr.min_opacity = -1
        attr.min_opacity = 256

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'alpha-gradient',
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

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'flower',
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

    tuples = utils.try_multiple_values(
        'flower',
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

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'flower',
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

    tuples = utils.try_multiple_values(
        'alpha-gradient',
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

    utils.try_multiple_values(
        'flower',
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

    utils.try_multiple_values(
        'flower',
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
        utils.try_multiple_values(
            'flower',
            [None],
            attr_callback=attr_callback)


# There's not much to test for create_rgba(), especially considering
# that we use it as part of most of the other tests. So let's skip it.
