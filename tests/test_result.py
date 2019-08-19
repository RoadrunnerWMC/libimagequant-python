import libimagequant as liq
import pytest

import utils


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

    tuples = utils.try_multiple_values(
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

    tuples = utils.try_multiple_values(
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

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
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

    utils.check_outputs_unique(utils.get_output_datas(utils.try_multiple_values(
        'flower.jpg',
        [0.01, 0.5, 0.99],
        result_callback=result_callback)))


def test_result_get_palette():
    """
    Test Result.get_palette()
    """

    (_, _, result, _), = utils.try_multiple_values(
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

    (_, image, result, _), = utils.try_multiple_values(
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
