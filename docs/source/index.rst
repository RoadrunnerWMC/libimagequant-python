libimagequant Python Bindings Documentation
===========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Welcome to the documentation for the unofficial Python bindings for
`libimagequant <https://pngquant.org/lib/>`_.

These bindings are designed to be Pythonic, yet still faithful to the C API.
Almost every C function can be used through the bindings. The Python classes
correspond directly to C structs, and each Python function represents one C
function. However, some changes have been made:

*   All functions have been made into class methods.
*   Functions that are effectively getters and setters for struct members are
    represented as class properties.
*   Values that are semantically boolean but are of the ``int`` type in C
    are given the Python :py:class:`bool` type.
*   Error-code return values are instead expressed by raising exceptions (see
    :ref:`exceptions`).
*   A few functions -- mostly ones that don't make much sense in Python -- are
    not supported (see :ref:`unsupported-functions`).

This documentation is intentionally terse, so as to avoid duplicating the
information in the official C API documentation. The recommended way to use
this page is to first peruse `the official libimagequant C API documentation
<https://pngquant.org/lib/>`_ to see how you could accomplish your goals in C,
and to then search for the C function names here to find the equivalent Python
APIs.

You may want to take a look at :ref:`examples`, :ref:`installation`, or the
:ref:`api-ref`.

You might also be interested in the companion library
`libimagequant_integrations <https://github.com/RoadrunnerWMC/libimagequant-python-integrations>`_,
which provides helper functions for using libimagequant with many other Python
libraries used for imagery.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _examples:

Examples
========

*Note:* instead of copypasting these examples in order to use libimagequant
with Pillow, consider using the
`libimagequant_integrations <https://github.com/RoadrunnerWMC/libimagequant-python-integrations>`_
library, which provides robust conversion functions for you.

Here's the simplest useful example, which uses `Pillow
<https://python-pillow.org/>`_ for loading/saving PNGs:

.. code-block:: python

    import libimagequant as liq
    import PIL.Image

    # Load the image with Pillow
    img = PIL.Image.open('input.png').convert('RGBA')

    # Create libimagequant Attr and Image objects from it
    attr = liq.Attr()
    input_image = attr.create_rgba(img.tobytes(), img.width, img.height, 0)

    # Quantize
    result = input_image.quantize(attr)

    # Get the quantization result
    out_pixels = result.remap_image(input_image)
    out_palette = result.get_palette()

    # Convert the output to a Pillow Image
    out_img = PIL.Image.frombytes('P', (img.width, img.height), out_pixels)
    palette_data = []
    for color in out_palette:
        palette_data.append(color.r)
        palette_data.append(color.g)
        palette_data.append(color.b)
    out_img.putpalette(palette_data)

    # Save it
    out_img.save('output.png')

And here's a port of `example.c from the libimagequant repository
<https://github.com/ImageOptim/libimagequant/blob/master/example.c>`_:

.. code-block:: python

    import sys

    import libimagequant as liq
    import PIL.Image


    def main(argv):
        if len(argv) < 2:
            print('Please specify a path to a PNG file', file=sys.stderr)
            return 1

        input_png_file_path = argv[1]

        # Load PNG file and decode it as raw RGBA pixels
        # This uses the Pillow library for PNG reading (not part of libimagequant)

        img = PIL.Image.open(input_png_file_path).convert('RGBA')
        width = img.width
        height = img.height
        input_rgba_pixels = img.tobytes()

        # Use libimagequant to make a palette for the RGBA pixels

        attr = liq.Attr()
        input_image = attr.create_rgba(input_rgba_pixels, width, height, 0)

        result = input_image.quantize(attr)

        # Use libimagequant to make new image pixels from the palette

        result.dithering_level = 1.0

        raw_8bit_pixels = result.remap_image(input_image)
        palette = result.get_palette()

        # Save converted pixels as a PNG file
        # This uses the Pillow library for PNG writing (not part of libimagequant)
        img = PIL.Image.frombytes('P', (width, height), raw_8bit_pixels)

        palette_data = []
        for color in palette:
            palette_data.append(color.r)
            palette_data.append(color.g)
            palette_data.append(color.b)
        img.putpalette(palette_data)

        output_png_file_path = 'quantized_example.png'
        img.save(output_png_file_path)

        print('Written ' + output_png_file_path)

        # Done.

    main(sys.argv)


.. _installation:

Installation
============

These bindings are built and tested against:

*   Supported versions of `CPython <https://www.python.org/>`_ 3 (3.5 through
    3.8, at the time of this writing)
*   A recent version of `PyPy <https://www.pypy.org>`_ in Python 3 mode.
    (Please note that the selected PyPy version may not be the latest, and may
    not be the same across all operating systems.)

(Python 2 is not supported.)

On the following platforms:

*    64-bit Windows
*    64-bit macOS
*    64-bit Linux (using the "manylinux2010" platform)

(The bindings should work on 32-bit systems, but builds for such platforms are
not provided.)

Builds are provided on PyPI for every combination of Python version and
platform listed above. If you're using any of those environments, the
recommended way to install is through pip. You can try running:

.. code-block:: text

    pip install libimagequant

If that doesn't work, you might have better luck with either of:

.. code-block:: text

    python3 -m pip install libimagequant

    py -3 -m pip install libimagequant

If for some reason you'd instead like to install from source (such as if you're
running a system for which official builds are not available on PyPI), read on.

Building from source
--------------------

To build from source, begin by cloning or downloading the repository.

If desired, you can replace the ``libimagequant`` folder with the latest
libimagequant source code from `its own repository
<https://github.com/ImageOptim/libimagequant>`_.

Install ``cffi``, ``setuptools`` and ``wheel`` on the Python interpreter you
want the bindings to be built against. For example,

.. code-block:: text

    python3 -m pip install --upgrade cffi setuptools wheel

Navigate (in a terminal) to the ``bindings`` directory, and run
``setup.py bdist_wheel`` with the Python interpreter you want the bindings to
be built against. For example,

.. code-block:: text

    python3 setup.py bdist_wheel

This should create (among other things) a ``dist`` folder with a ``.whl``
(wheel) file inside. You can now install that wheel file with pip, or
distribute it.


.. _api-ref:

API reference
=============


.. _exceptions:

Exceptions
----------

Many functions in libimagequant's C API use ``liq_error`` enum return values to
indicate success or errors. Since it is more Pythonic to use exceptions for
this, the Python bindings for those functions convert those return values to
exceptions, which you can catch using ``try``/``except``. The following table
outlines how they're mapped:

+------------------------------+---------------------------------------------------+
| ``liq_error`` value          | Python exception                                  |
+==============================+===================================================+
| ``LIQ_OK``                   | *(n/a)*                                           |
+------------------------------+---------------------------------------------------+
| ``LIQ_QUALITY_TOO_LOW``      | :py:class:`libimagequant.QualityTooLowError`      |
+------------------------------+---------------------------------------------------+
| ``LIQ_VALUE_OUT_OF_RANGE``   | :py:class:`ValueError`                            |
+------------------------------+---------------------------------------------------+
| ``LIQ_OUT_OF_MEMORY``        | :py:class:`MemoryError`                           |
+------------------------------+---------------------------------------------------+
| ``LIQ_ABORTED``              | :py:class:`libimagequant.AbortedError`            |
+------------------------------+---------------------------------------------------+
| ``LIQ_BITMAP_NOT_AVAILABLE`` | :py:class:`libimagequant.BitmapNotAvailableError` |
+------------------------------+---------------------------------------------------+
| ``LIQ_BUFFER_TOO_SMALL``     | :py:class:`libimagequant.BufferTooSmallError`     |
+------------------------------+---------------------------------------------------+
| ``LIQ_INVALID_POINTER``      | :py:class:`RuntimeError`                          |
+------------------------------+---------------------------------------------------+
| ``LIQ_UNSUPPORTED``          | :py:class:`libimagequant.UnsupportedError`        |
+------------------------------+---------------------------------------------------+


Constants
---------

.. data:: libimagequant.LIQ_VERSION and libimagequant.LIQ_VERSION_STRING

    Information about the version of **libimagequant** currently in use.

    Depending on your use case, you may want to use :py:data:`BINDINGS_VERSION`
    and :py:data:`BINDINGS_VERSION_STRING` instead.

    Python equivalents of ``LIQ_VERSION`` and ``LIQ_VERSION_STRING``.

.. data:: libimagequant.BINDINGS_VERSION and libimagequant.BINDINGS_VERSION_STRING

    Information about the version of the **Python bindings** currently in use.
    
    The bindings version is the version of libimagequant the bindings were
    designed for, with an additional version segment (usually ``.0``). For
    example, for the bindings release designed for libimagequant 2.12.5,
    ``BINDINGS_VERSION`` and ``BINDINGS_VERSION_STRING`` would be 2120500 and
    ``'2.12.5.0'``, respectively.

    This will often match :py:data:`LIQ_VERSION` and
    :py:data:`LIQ_VERSION_STRING` (up to the extra segment), but is not
    guaranteed to always do so.

    Depending on your use case, you may want to use :py:data:`LIQ_VERSION` and
    :py:data:`LIQ_VERSION_STRING` instead.


Classes
-------


.. py:class:: libimagequant.Attr

    Python equivalent of the ``liq_attr`` struct.
    
    The constructor for this class is the equivalent of ``liq_attr_create()``.
    ``liq_attr_destroy()`` is handled automatically.

    .. py:attribute:: max_colors

        Python equivalent of ``liq_get_max_colors()`` and
        ``liq_set_max_colors()``.

        :type: :py:class:`int`

    .. py:attribute:: speed

        Python equivalent of ``liq_get_speed()`` and ``liq_set_speed()``.

        :type: :py:class:`int`

    .. py:attribute:: min_opacity

        Python equivalent of ``liq_get_min_opacity()`` and
        ``liq_set_min_opacity()``.

        :type: :py:class:`int`

    .. py:attribute:: min_posterization

        Python equivalent of ``liq_get_min_posterization()`` and
        ``liq_set_min_posterization()``.

        :type: :py:class:`int`

    .. py:attribute:: min_quality

        Python equivalent of ``liq_get_min_quality()`` and (along with
        :py:attr:`max_quality`) ``liq_set_quality()``.

        :type: :py:class:`int`

    .. py:attribute:: max_quality

        Python equivalent of ``liq_get_max_quality()`` and (along with
        :py:attr:`min_quality`) ``liq_set_quality()``.

        :type: :py:class:`int`

    .. py:attribute:: last_index_transparent

        Python equivalent of ``liq_set_last_index_transparent()``.

        For consistency with the C API, this is a write-only property.

        .. note::

            Since the only meaningful values for this variable in the C API are
            "zero" and "non-zero," it is presented as a :py:class:`bool` in
            these Python bindings.

        :type: :py:class:`bool`

    .. py:function:: copy() -> Attr

        Python equivalent of ``liq_attr_copy()``.

        :returns: A copy of this object.
        :rtype: :py:class:`libimagequant.Attr`

    .. py:function:: create_rgba(bitmap: bytes, width: int, height: int, gamma: float) -> Image

        Python equivalent of ``liq_image_create_rgba()``.

        :returns: The new image created from the provided data.
        :rtype: :py:class:`libimagequant.Image`

    .. py:function:: set_log_callback(log_callback_function: Callable[[Attr, str, object], None], user_info: object)

        Python equivalent of ``liq_set_log_callback()``.

        The signature of the callback function should be
        ``callback(attr: Attr, message: str, user_info: object)``.

        The ``user_info`` parameter can be any Python object, which will be
        passed to the callback as its third argument.

        Call this function with ``log_callback_function = None`` to clear the
        callback.

    .. py:function:: set_progress_callback(progress_callback_function: Callable[[float, object], bool], user_info: object)

        Python equivalent of ``liq_attr_set_progress_callback()``.

        The signature of the callback function should be
        ``callback(progress_percent: float, user_info: object) -> bool``. If it
        returns ``False``, the quantization operation will be aborted (causing
        :py:class:`AbortedException` to be raised); thus, you should normally
        return ``True`` from the callback in order for the operation to
        proceed.

        The ``user_info`` parameter can be any Python object, which will be
        passed to the callback as its third argument.

        Call this function with ``progress_callback_function = None`` to clear
        the callback.


.. py:class:: libimagequant.Histogram(attr: Attr)

    Python equivalent of the ``liq_histogram`` struct.
    
    The constructor for this class is the equivalent of
    ``liq_histogram_create()``. ``liq_histogram_destroy()`` is handled
    automatically.

    .. py:function:: add_image(attr: Attr, image: Image)

        Python equivalent of ``liq_histogram_add_image()``.

    .. py:function:: add_colors(attr: Attr, entries: List[HistogramEntry], gamma: float)

        Python equivalent of ``liq_histogram_add_colors()``.

    .. py:function:: add_fixed_color(color: Color, gamma: float)

        Python equivalent of ``liq_histogram_add_fixed_color()``.

    .. py:function:: quantize(options: Attr) -> Result

        Python equivalent of ``liq_histogram_quantize()``.

        :returns: The result of the quantization.
        :rtype: :py:class:`libimagequant.Result`


.. py:class:: libimagequant.HistogramEntry(color: Color, count: int)

    Python equivalent of the ``liq_histogram_entry`` struct.

    .. py:attribute:: color

        Python equivalent of the ``liq_histogram.color`` member.

        :type: :py:class:`libimagequant.Color`

    .. py:attribute:: count

        Python equivalent of the ``liq_histogram.count`` member.

        :type: :py:class:`int`


.. py:class:: libimagequant.Image

    Python equivalent of the ``liq_image`` struct.
    
    This class cannot be instantiated directly. Use
    :py:func:`Image.create_rgba` to create it.
    
    ``liq_image_destroy()`` is handled automatically.

    .. py:attribute:: width

        Python equivalent of ``liq_image_get_width()``.

        This is a read-only property.

        :type: :py:class:`int`

    .. py:attribute:: height

        Python equivalent of ``liq_image_get_height()``.

        This is a read-only property.

        :type: :py:class:`int`

    .. py:attribute:: background

        Python equivalent of ``liq_image_set_background()``.

        For consistency with the C API, this is a write-only property.

        :type: :py:class:`libimagequant.Image`

    .. py:attribute:: importance_map

        Python equivalent of ``liq_image_set_importance_map()``.

        For consistency with the C API, this is a write-only property.

        :type: :py:class:`bytes`

    .. py:function:: add_fixed_color(color: Color)

        Python equivalent of ``liq_image_add_fixed_color()``.

    .. py:function:: quantize(options: Attr) -> Result

        Python equivalent of ``liq_image_quantize()``.

        :returns: The result of the quantization.
        :rtype: :py:class:`libimagequant.Result`


.. py:class:: libimagequant.Result

    Python equivalent of the ``liq_result`` struct.
    
    This class cannot be instantiated directly. Use
    :py:func:`Histogram.quantize` or :py:func:`Image.quantize` to create it.
    
    ``liq_result_destroy()`` is handled automatically.

    .. py:attribute:: dithering_level

        Python equivalent of ``liq_set_dithering_level()``.

        For consistency with the C API, this is a write-only property.

        :type: :py:class:`float`

    .. py:attribute:: output_gamma

        Python equivalent of ``liq_get_output_gamma()`` and
        ``liq_set_output_gamma()``.

        :type: :py:class:`float`

    .. py:attribute:: quantization_error

        Python equivalent of ``liq_get_quantization_error()``.

        This is a read-only property.

        :type: :py:class:`float`

    .. py:attribute:: quantization_quality

        Python equivalent of ``liq_get_quantization_quality()``.

        This is a read-only property.

        :type: :py:class:`int`

    .. py:attribute:: remapping_error

        Python equivalent of ``liq_get_remapping_error()``.

        This is a read-only property.

        :type: :py:class:`float`

    .. py:attribute:: remapping_quality

        Python equivalent of ``liq_get_remapping_quality()``.

        This is a read-only property.

        :type: :py:class:`int`

    .. py:function:: get_palette() -> List[Color]

        Python equivalent of ``liq_get_palette()``.

        :returns: The list of colors.
        :rtype: :py:class:`list` of :py:class:`libimagequant.Color`\s

    .. py:function:: remap_image(input_image: Image) -> bytes

        Python equivalent of ``liq_write_remapped_image()``.

        :returns: The pixel data for the remapped image.
        :rtype: :py:class:`bytes`

    .. py:function:: set_progress_callback(progress_callback_function: Callable[[float, object], bool], user_info: object)

        Python equivalent of ``liq_result_set_progress_callback()``.

        The signature of the callback function should be
        ``callback(progress_percent: float, user_info: object) -> bool``. If it
        returns ``False``, the remapping operation will be aborted (causing
        :py:class:`AbortedException` to be raised); thus, you should normally
        return ``True`` from the callback in order for the operation to
        proceed.

        The ``user_info`` parameter can be any Python object, which will be
        passed to the callback as its third argument.

        Call this function with ``progress_callback_function = None`` to clear
        the callback.

.. py:class:: libimagequant.Color

    Python equivalent of the ``liq_color`` struct.

    This is simply a `collections.namedtuple
    <https://docs.python.org/3/library/collections.html#collections.namedtuple>`_
    with ``r``, ``g``, ``b``, and ``a`` fields.

    Please note that the equivalent of a ``liq_palette`` struct in these
    bindings is a :py:class:`list` of instances of this class.


.. _unsupported-functions:

Functions with no direct Python equivalent
==========================================

*   ``liq_attr_create_with_allocator()``

    Although "custom allocators" aren't *completely* meaningless in Python
    (in the context of cffi, in particular), it's an extremely uncommon case.
    
    If you have a legitimate need for this feature, please open an issue (or,
    better, a pull request!). For 99% of cases, :py:class:`Attr`'s default
    constructor (corresponding to ``liq_attr_create()``) should suffice.

*   ``liq_set_log_flush_callback()``

    This is unsupported due to issues that arise due to Python's garbage
    collection. Since functions in Python are objects that get
    garbage-collected like all other types, there is no guarantee that the
    callback will actually still exist when the :py:class:`Attr` object is
    deleted. This can lead to very weird and inconsistent issues.

    Since libimagequant is totally synchronous, the recommended workaround is
    to simply flush any logging resources after you finish using your
    libimagequant objects.

*   ``liq_image_create_rgba_rows()`` and ``liq_image_create_custom()``

    These are unsupported because Python does not allow for the fine-grained
    raw pointer access that would make these functions useful.

    Use :py:func:`Image.create_rgba()` (corresponding to
    ``liq_image_create_rgba()``) instead.

*   ``liq_image_set_memory_ownership()``

    This is unsupported because it's too low-level of a concern to expose to
    Python programs. Ensuring that memory is managed properly is the
    responsibility of the bindings themselves, not your application.

*   ``liq_write_remapped_image_rows()``

    This is unsupported because Python does not allow for the fine-grained raw
    pointer access that would make it useful.

    Use :py:func:`Result.remap_image()` (corresponding to
    ``liq_write_remapped_image()``) instead.

*   ``liq_version()``

    Use :py:data:`LIQ_VERSION` or :py:data:`BINDINGS_VERSION` instead,
    depending on if you need to check the libimagequant version or the Python
    bindings version.

*   ``liq_quantize_image()``

    This is unsupported because it is deprecated in the C API. Use
    :py:func:`Image.quantize()` (corresponding to ``liq_image_quantize()``)
    instead.
