import functools
import os, os.path
import struct
import zlib

import libimagequant as liq


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
    with open(os.path.join(os.path.dirname(__file__), 'res', name + '.raw'), 'rb') as f:
        width, height = struct.unpack_from('<II', f.read(8))
        return width, height, zlib.decompress(f.read())


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
