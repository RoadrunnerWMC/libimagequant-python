import collections
from typing import Callable, List

from ._libimagequant import lib, ffi


LIQ_VERSION = lib.liq_version()
LIQ_VERSION_STRING = ffi.string(lib._py_get_liq_version_string()).decode('ascii')
BINDINGS_VERSION = 2140100
BINDINGS_VERSION_STRING = '2.14.1.0'


########################################################################
############################## Exceptions ##############################
########################################################################


class QualityTooLowError(Exception):
    """
    Equivalent to LIQ_QUALITY_TOO_LOW
    """
    pass

class AbortedError(Exception):
    """
    Equivalent to LIQ_ABORTED
    """
    pass

class BitmapNotAvailableError(Exception):
    """
    Equivalent to LIQ_BITMAP_NOT_AVAILABLE
    """
    pass

class BufferTooSmallError(Exception):
    """
    Equivalent to LIQ_BUFFER_TOO_SMALL
    """
    pass

class UnsupportedError(Exception):
    """
    Equivalent to LIQ_UNSUPPORTED
    """
    pass

def _check_ret(value):
    """
    Check the provided liq_error int value, and raise the appropriate
    corresponding Python exception if it's not LIQ_OK
    """
    if value == lib.LIQ_OK:
        pass
    elif value == lib.LIQ_QUALITY_TOO_LOW:
        raise QualityTooLowError
    elif value == lib.LIQ_VALUE_OUT_OF_RANGE:
        raise ValueError
    elif value == lib.LIQ_OUT_OF_MEMORY:
        raise MemoryError
    elif value == lib.LIQ_ABORTED:
        raise AbortedError
    elif value == lib.LIQ_BITMAP_NOT_AVAILABLE:
        raise BitmapNotAvailableError
    elif value == lib.LIQ_BUFFER_TOO_SMALL:
        raise BufferTooSmallError
    elif value == lib.LIQ_INVALID_POINTER:
        # Either there's a bug in the bindings, or someone is messing
        # with the ._c attributes directly. Either way, fail
        raise RuntimeError('LIQ_INVALID_POINTER')
    elif value == lib.LIQ_UNSUPPORTED:
        raise UnsupportedError
    else:
        # (this definitely shouldn't happen)
        raise RuntimeError


########################################################################
############################### Callbacks ##############################
########################################################################


@ffi.def_extern()
def _py_liq_log_callback_function_impl(attr_raw, message_raw, user_info_raw):
    """
    Handler for all liq_log_callback_function callbacks
    """
    attr = ffi.from_handle(user_info_raw)
    message = ffi.string(message_raw).decode('ascii')
    attr._log_callback_function(attr, message, attr._log_callback_user_info)


@ffi.def_extern()
def _py_liq_progress_callback_function_impl(progress_percent, user_info_raw):
    """
    Handler for all liq_progress_callback_function callbacks
    (both for Attr and Result)
    """
    obj = ffi.from_handle(user_info_raw) # either an Attr or a Result object
    return 1 if obj._progress_callback_function(progress_percent, obj._progress_callback_user_info) else 0


########################################################################
################################ Classes ###############################
########################################################################


Color = collections.namedtuple('Color', ['r', 'g', 'b', 'a'])

def _color_to_c(color: Color):
    c = ffi.new('liq_color *')[0]
    c.r = color.r
    c.g = color.g
    c.b = color.b
    c.a = color.a
    return c

def _c_to_color(c):
    return Color(c.r, c.g, c.b, c.a)


class HistogramEntry:
    _c = None
    color = None
    count = None

    def __init__(self, color: Color, count: int):
        self._c = ffi.new('liq_histogram_entry *')[0]
        self.color = color
        self.count = count

    @property
    def color(self):
        return _c_to_color(self._c.color)
    @color.setter
    def color(self, value: Color):
        self._c.color = _color_to_c(value)

    @property
    def count(self):
        return self._c.count
    @count.setter
    def count(self, value: int):
        self._c.count = value


class Attr:
    _c = None

    _log_callback_function = None
    _log_callback_user_info = None
    _progress_callback_function = None
    _progress_callback_user_info = None

    def __init__(self, *, _c=None):
        if _c is None:
            _c = ffi.gc(lib.liq_attr_create(), lib.liq_attr_destroy)

        self._c = _c

    _handle = None
    def _get_self_handle(self):
        if self._handle is None:
            self._handle = ffi.new_handle(self)
        return self._handle

    def copy(self) -> 'Attr':
        new = Attr()
        new._c = ffi.gc(lib.liq_attr_copy(self._c), lib.liq_attr_destroy)
        new._log_callback_function = self._log_callback_function
        new._log_callback_user_info = self._log_callback_user_info
        new._progress_callback_function = self._progress_callback_function
        new._progress_callback_user_info = self._progress_callback_user_info
        return new

    @property
    def max_colors(self):
        return lib.liq_get_max_colors(self._c)
    @max_colors.setter
    def max_colors(self, value: int):
        _check_ret(lib.liq_set_max_colors(self._c, value))

    @property
    def speed(self):
        return lib.liq_get_speed(self._c)
    @speed.setter
    def speed(self, value: int):
        _check_ret(lib.liq_set_speed(self._c, value))

    @property
    def min_opacity(self):
        return lib.liq_get_min_opacity(self._c)
    @min_opacity.setter
    def min_opacity(self, value: int):
        _check_ret(lib.liq_set_min_opacity(self._c, value))

    @property
    def min_posterization(self):
        return lib.liq_get_min_posterization(self._c)
    @min_posterization.setter
    def min_posterization(self, value: int):
        _check_ret(lib.liq_set_min_posterization(self._c, value))

    @property
    def min_quality(self):
        return lib.liq_get_min_quality(self._c)
    @min_quality.setter
    def min_quality(self, value: int):
        _check_ret(lib.liq_set_quality(self._c, value, self.max_quality))

    @property
    def max_quality(self):
        return lib.liq_get_max_quality(self._c)
    @max_quality.setter
    def max_quality(self, value: int):
        _check_ret(lib.liq_set_quality(self._c, self.min_quality, value))

    def last_index_transparent(self, value: bool):
        lib.liq_set_last_index_transparent(self._c, 1 if value else 0)
    last_index_transparent = property(None, last_index_transparent) # setter only

    def set_log_callback(self, log_callback_function: Callable[['Attr', str, object], None], user_info: object):
        self._log_callback_function = log_callback_function
        self._log_callback_user_info = user_info

        if log_callback_function is None:
            lib.liq_set_log_callback(self._c, ffi.NULL, ffi.NULL)
        else:
            lib.liq_set_log_callback(self._c, lib._py_liq_log_callback_function_impl, self._get_self_handle())

    # liq_set_log_flush_callback is not supported (due to dtor-related issues in Python)

    def set_progress_callback(self, progress_callback_function: Callable[[float, object], bool], user_info: object):
        self._progress_callback_function = progress_callback_function
        self._progress_callback_user_info = user_info

        if progress_callback_function is None:
            lib.liq_attr_set_progress_callback(self._c, ffi.NULL, ffi.NULL)
        else:
            lib.liq_attr_set_progress_callback(self._c, lib._py_liq_progress_callback_function_impl, self._get_self_handle())

    # liq_image_create_rgba_rows is not supported

    def create_rgba(self, bitmap: bytes, width: int, height: int, gamma: float) -> 'Image':
        # We need to use img._destroy() as the ffi.gc() destructor
        # callback, but the Image constructor wants the _c object. So we
        # give it a fake one and then monkeypatch the true _c object
        # into the Image afterwards.
        img = Image(_c=object())
        img._c = ffi.gc(lib.liq_image_create_rgba(self._c, ffi.from_buffer(bitmap), width, height, gamma), img._destroy)
        img._bitmap = bitmap # to prevent it from being GC'd
        return img

    # liq_image_create_custom is not supported


class Image:
    _c = None
    _is_background = False

    def __init__(self, *, _c=None):
        if _c is None:
            raise RuntimeError('libimagequant.Image constructor called without _c')

        self._c = _c

    def background(self, background_image: 'Image'):
        _check_ret(lib.liq_image_set_background(self._c, background_image._c))
        background_image._is_background = True
    background = property(None, background) # setter only

    def importance_map(self, buffer: bytes):
        _check_ret(lib.liq_image_set_importance_map(self._c, ffi.from_buffer(buffer), len(buffer), lib.LIQ_COPY_PIXELS))
    importance_map = property(None, importance_map) # setter only

    def add_fixed_color(self, color: Color):
        _check_ret(lib.liq_image_add_fixed_color(self._c, _color_to_c(color)))

    @property
    def width(self):
        return lib.liq_image_get_width(self._c)

    @property
    def height(self):
        return lib.liq_image_get_height(self._c)

    def quantize(self, options: Attr) -> 'Result':
        result_c = ffi.new('liq_result **')
        _check_ret(lib.liq_image_quantize(self._c, options._c, result_c))
        return Result(_c=ffi.gc(result_c[0], lib.liq_result_destroy))

    def _destroy(self, obj):
        """
        Since liq_image_destroy(img) automatically destroys
        img->background in addition to img, we need to avoid calling
        liq_image_destroy() on ourselves if we're the ->background of
        some other Image object.
        Otherwise LIQ complains about use-after-free and/or we get
        occasional segfaults after using the Image.background property.
        """
        if not self._is_background:
            lib.liq_image_destroy(obj)


class Result:
    _c = None

    _progress_callback_function = None
    _progress_callback_user_info = None

    def __init__(self, *, _c=None):
        if _c is None:
            raise RuntimeError('libimagequant.Result constructor called without _c')

        self._c = _c

    _handle = None
    def _get_self_handle(self):
        if self._handle is None:
            self._handle = ffi.new_handle(self)
        return self._handle

    def set_progress_callback(self, progress_callback_function: Callable[[float, object], bool], user_info: object):
        self._progress_callback_function = progress_callback_function
        self._progress_callback_user_info = user_info

        if progress_callback_function is None:
            lib.liq_result_set_progress_callback(self._c, ffi.NULL, ffi.NULL)
        else:
            lib.liq_result_set_progress_callback(self._c, lib._py_liq_progress_callback_function_impl, self._get_self_handle())

    def dithering_level(self, value: float):
        _check_ret(lib.liq_set_dithering_level(self._c, value))
    dithering_level = property(None, dithering_level) # setter only

    @property
    def output_gamma(self):
        return lib.liq_get_output_gamma(self._c)
    @output_gamma.setter
    def output_gamma(self, value: float):
        _check_ret(lib.liq_set_output_gamma(self._c, value))

    @property
    def quantization_error(self):
        return lib.liq_get_quantization_error(self._c)

    @property
    def quantization_quality(self):
        return lib.liq_get_quantization_quality(self._c)

    @property
    def remapping_error(self):
        return lib.liq_get_remapping_error(self._c)

    @property
    def remapping_quality(self):
        return lib.liq_get_remapping_quality(self._c)

    def get_palette(self) -> List[Color]:
        palette_raw = lib.liq_get_palette(self._c)
        return [_c_to_color(palette_raw.entries[i]) for i in range(palette_raw.count)]

    def remap_image(self, input_image: Image) -> bytes:
        buffer = ffi.new('unsigned char[%d]' % (input_image.width * input_image.height))
        _check_ret(lib.liq_write_remapped_image(self._c, input_image._c, buffer, len(buffer)))
        return bytes(buffer)


class Histogram:
    _c = None

    def __init__(self, attr: Attr):
        self._c = ffi.gc(lib.liq_histogram_create(attr._c), lib.liq_histogram_destroy)

    def add_image(self, attr: Attr, image: Image):
        _check_ret(lib.liq_histogram_add_image(self._c, attr._c, image._c))

    def add_colors(self, attr: Attr, entries: List[HistogramEntry], gamma: float):
        _check_ret(lib.liq_histogram_add_colors(self._c, attr._c, [e._c for e in entries], len(entries), gamma))

    def add_fixed_color(self, color: Color, gamma: float):
        _check_ret(lib.liq_histogram_add_fixed_color(self._c, _color_to_c(color), gamma))
        
    def quantize(self, options: Attr) -> Result:
        result_c = ffi.new('liq_result **')
        _check_ret(lib.liq_histogram_quantize(self._c, options._c, result_c))
        return Result(_c=ffi.gc(result_c[0], lib.liq_result_destroy))
