# Installing Pillow on all platforms we hope to support is difficult.
# So instead, we run this script beforehand to convert all of the test
# cases (png/jpg) to raw data files that can be easily loaded on any
# system without requiring Pillow. These raw files are checked into the
# repository.

import pathlib
import struct
import zlib

import PIL.Image


def do_conversion(fp):
    """
    Create the .raw file for the file at fp (pathlib.Path)
    """
    img = PIL.Image.open(str(fp)).convert('RGBA')

    with open(fp.with_suffix('.raw'), 'wb') as f:
        f.write(struct.pack('<II', img.width, img.height))
        f.write(zlib.compress(img.tobytes()))


for fp in pathlib.Path('.').glob('*.png'):
    do_conversion(fp)
for fp in pathlib.Path('.').glob('*.jpg'):
    do_conversion(fp)
