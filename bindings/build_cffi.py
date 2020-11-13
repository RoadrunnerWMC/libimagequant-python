import sys

from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef(
"""
    typedef struct liq_attr liq_attr;
    typedef struct liq_image liq_image;
    typedef struct liq_result liq_result;
    typedef struct liq_histogram liq_histogram;

    typedef struct liq_color {
        unsigned char r, g, b, a;
    } liq_color;

    typedef struct liq_palette {
        unsigned int count;
        liq_color entries[256];
    } liq_palette;

    typedef enum liq_error {
        LIQ_OK = 0,
        LIQ_QUALITY_TOO_LOW = 99,
        LIQ_VALUE_OUT_OF_RANGE = 100,
        LIQ_OUT_OF_MEMORY,
        LIQ_ABORTED,
        LIQ_BITMAP_NOT_AVAILABLE,
        LIQ_BUFFER_TOO_SMALL,
        LIQ_INVALID_POINTER,
        LIQ_UNSUPPORTED,
    } liq_error;

    enum liq_ownership {
        LIQ_OWN_ROWS=4,
        LIQ_OWN_PIXELS=8,
        LIQ_COPY_PIXELS=16,
    };

    typedef struct liq_histogram_entry {
        liq_color color;
        unsigned int count;
    } liq_histogram_entry;

    extern liq_attr* liq_attr_create(void);
    extern liq_attr* liq_attr_create_with_allocator(void* (*malloc)(size_t), void (*free)(void*));
    extern liq_attr* liq_attr_copy(const liq_attr *orig);
    extern void liq_attr_destroy(liq_attr *attr);

    extern liq_histogram* liq_histogram_create(const liq_attr* attr);
    extern liq_error liq_histogram_add_image(liq_histogram *hist, const liq_attr *attr, liq_image* image);
    extern liq_error liq_histogram_add_colors(liq_histogram *hist, const liq_attr *attr, const liq_histogram_entry entries[], int num_entries, double gamma);
    extern liq_error liq_histogram_add_fixed_color(liq_histogram *hist, liq_color color, double gamma);
    extern void liq_histogram_destroy(liq_histogram *hist);

    extern liq_error liq_set_max_colors(liq_attr* attr, int colors);
    extern int liq_get_max_colors(const liq_attr* attr);
    extern liq_error liq_set_speed(liq_attr* attr, int speed);
    extern int liq_get_speed(const liq_attr* attr);
    extern liq_error liq_set_min_opacity(liq_attr* attr, int min);
    extern int liq_get_min_opacity(const liq_attr* attr);
    extern liq_error liq_set_min_posterization(liq_attr* attr, int bits);
    extern int liq_get_min_posterization(const liq_attr* attr);
    extern liq_error liq_set_quality(liq_attr* attr, int minimum, int maximum);
    extern int liq_get_min_quality(const liq_attr* attr);
    extern int liq_get_max_quality(const liq_attr* attr);
    extern void liq_set_last_index_transparent(liq_attr* attr, int is_last);

    typedef void liq_log_callback_function(const liq_attr*, const char *message, void* user_info);
    typedef void liq_log_flush_callback_function(const liq_attr*, void* user_info);
    extern void liq_set_log_callback(liq_attr*, liq_log_callback_function*, void* user_info);
    extern void liq_set_log_flush_callback(liq_attr*, liq_log_flush_callback_function*, void* user_info);

    typedef int liq_progress_callback_function(float progress_percent, void* user_info);
    extern void liq_attr_set_progress_callback(liq_attr*, liq_progress_callback_function*, void* user_info);
    extern void liq_result_set_progress_callback(liq_result*, liq_progress_callback_function*, void* user_info);

    // The rows and their data are not modified. The type of `rows` is non-const only due to a bug in C's typesystem design.
    extern liq_image *liq_image_create_rgba_rows(const liq_attr *attr, void *const rows[], int width, int height, double gamma);
    extern liq_image *liq_image_create_rgba(const liq_attr *attr, const void *bitmap, int width, int height, double gamma);

    typedef void liq_image_get_rgba_row_callback(liq_color row_out[], int row, int width, void* user_info);
    extern liq_image *liq_image_create_custom(const liq_attr *attr, liq_image_get_rgba_row_callback *row_callback, void* user_info, int width, int height, double gamma);

    extern liq_error liq_image_set_memory_ownership(liq_image *image, int ownership_flags);
    extern liq_error liq_image_set_background(liq_image *img, liq_image *background_image);
    extern liq_error liq_image_set_importance_map(liq_image *img, unsigned char buffer[], size_t buffer_size, enum liq_ownership memory_handling);
    extern liq_error liq_image_add_fixed_color(liq_image *img, liq_color color);
    extern int liq_image_get_width(const liq_image *img);
    extern int liq_image_get_height(const liq_image *img);
    extern void liq_image_destroy(liq_image *img);

    extern liq_error liq_histogram_quantize(liq_histogram *const input_hist, liq_attr *const options, liq_result **result_output);
    extern liq_error liq_image_quantize(liq_image *const input_image, liq_attr *const options, liq_result **result_output);

    extern liq_error liq_set_dithering_level(liq_result *res, float dither_level);
    extern liq_error liq_set_output_gamma(liq_result* res, double gamma);
    extern double liq_get_output_gamma(const liq_result *result);

    extern const liq_palette *liq_get_palette(liq_result *result);

    extern liq_error liq_write_remapped_image(liq_result *result, liq_image *input_image, void *buffer, size_t buffer_size);
    extern liq_error liq_write_remapped_image_rows(liq_result *result, liq_image *input_image, unsigned char **row_pointers);

    extern double liq_get_quantization_error(const liq_result *result);
    extern int liq_get_quantization_quality(const liq_result *result);
    extern double liq_get_remapping_error(const liq_result *result);
    extern int liq_get_remapping_quality(const liq_result *result);

    extern void liq_result_destroy(liq_result *);

    extern int liq_version(void);
""")

ffibuilder.cdef(
"""
    extern "Python" void _py_liq_log_callback_function_impl(const liq_attr*, const char *message, void* user_info);
    extern "Python" int _py_liq_progress_callback_function_impl(float progress_percent, void* user_info);

    static const char *_py_get_liq_version_string();
""")

ffibuilder.set_source('libimagequant._libimagequant',  # name of the output C extension
"""
    #include "libimagequant.h"

    static const char *_py_get_liq_version_string() {
        return LIQ_VERSION_STRING;
    }
""",
    sources=['libimagequant_c/blur.c',
             'libimagequant_c/kmeans.c',
             'libimagequant_c/libimagequant.c',
             'libimagequant_c/mediancut.c',
             'libimagequant_c/mempool.c',
             'libimagequant_c/nearest.c',
             'libimagequant_c/pam.c'],
    extra_compile_args=['-std=c99'],
    include_dirs=['libimagequant_c'])

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
