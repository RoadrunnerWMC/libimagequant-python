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