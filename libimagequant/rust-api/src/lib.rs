//! https://pngquant.org/lib/
//!
//! Converts RGBA images to 8-bit with alpha channel.
//!
//! This is based on imagequant library, which generates very high quality images.
//!
//! See `examples/` directory for example code.
#![doc(html_logo_url = "https://pngquant.org/pngquant-logo.png")]
#![warn(missing_docs)]

pub use crate::ffi::liq_error;
pub use crate::ffi::liq_error::*;

use fallible_collections::FallibleVec;
use imagequant_sys as ffi;
use std::fmt;
use std::marker::PhantomData;
use std::mem::MaybeUninit;
use std::mem;
use std::os::raw::{c_int, c_void};
use std::ptr;

pub use rgb::RGBA8 as RGBA;

/// Allocates all memory used by the library, like [`libc::malloc`].
///
/// Must return properly aligned memory (16-bytes on x86, pointer size on other architectures).
pub type MallocUnsafeFn = unsafe extern "C" fn(size: usize) -> *mut c_void;

/// Frees all memory used by the library, like [`libc::free`].
pub type FreeUnsafeFn = unsafe extern "C" fn(*mut c_void);

/// 8-bit RGBA. This is the only color format used by the library.
pub type Color = ffi::liq_color;

/// Number of pixels in a given color
///
/// Used if you're building histogram manually. Otherwise see `add_image()`
pub type HistogramEntry = ffi::liq_histogram_entry;

/// Settings for the conversion process. Start here.
pub struct Attributes {
    handle: *mut ffi::liq_attr,
    malloc: MallocUnsafeFn,
    free: FreeUnsafeFn,
}

/// Describes image dimensions for the library.
pub struct Image<'a> {
    handle: *mut ffi::liq_image,
    /// Holds row pointers for images with stride
    _marker: PhantomData<&'a [u8]>,
}

/// Palette inside.
pub struct QuantizationResult {
    handle: *mut ffi::liq_result,
}

/// Generate one shared palette for multiple images.
pub struct Histogram<'a> {
    attr: &'a Attributes,
    handle: *mut ffi::liq_histogram,
}

impl Drop for Attributes {
    #[inline]
    fn drop(&mut self) {
        unsafe {
            if !self.handle.is_null() {
                ffi::liq_attr_destroy(&mut *self.handle);
            }
        }
    }
}

impl<'a> Drop for Image<'a> {
    #[inline]
    fn drop(&mut self) {
        unsafe {
            ffi::liq_image_destroy(&mut *self.handle);
        }
    }
}

impl Drop for QuantizationResult {
    #[inline]
    fn drop(&mut self) {
        unsafe {
            ffi::liq_result_destroy(&mut *self.handle);
        }
    }
}

impl<'a> Drop for Histogram<'a> {
    #[inline]
    fn drop(&mut self) {
        unsafe {
            ffi::liq_histogram_destroy(&mut *self.handle);
        }
    }
}

impl Clone for Attributes {
    #[inline]
    fn clone(&self) -> Attributes {
        unsafe {
            Attributes {
                handle: ffi::liq_attr_copy(&*self.handle),
                malloc: self.malloc,
                free: self.free,
            }
        }
    }
}

impl Default for Attributes {
    #[inline(always)]
    fn default() -> Attributes {
        Attributes::new()
    }
}

impl Attributes {
    /// New handle for library configuration
    ///
    /// See also `new_image()`
    #[inline]
    #[must_use]
    pub fn new() -> Self {
        let handle = unsafe { ffi::liq_attr_create() };
        assert!(!handle.is_null(), "SSE-capable CPU is required for this build.");
        Attributes {
            handle,
            malloc: libc::malloc,
            free: libc::free,
        }
    }

    /// New handle for library configuration, with specified custom allocator for internal use.
    /// 
    /// See also `new_image()`
    /// 
    /// # Safety
    /// 
    /// * `malloc` and `free` must behave according to their corresponding C specification.
    /// * `malloc` must return properly aligned memory (16-bytes on x86, pointer-sized on other architectures).
    #[inline]
    #[must_use]
    pub unsafe fn with_allocator(malloc: MallocUnsafeFn, free: FreeUnsafeFn) -> Self {
        let handle = ffi::liq_attr_create_with_allocator(malloc, free);
        assert!(!handle.is_null(), "SSE-capable CPU is required for this build.");
        Attributes { handle, malloc, free }
    }

    /// It's better to use `set_quality()`
    #[inline]
    pub fn set_max_colors(&mut self, value: i32) -> liq_error {
        unsafe { ffi::liq_set_max_colors(&mut *self.handle, value) }
    }

    /// Number of least significant bits to ignore.
    ///
    /// Useful for generating palettes for VGA, 15-bit textures, or other retro platforms.
    #[inline]
    pub fn set_min_posterization(&mut self, value: i32) -> liq_error {
        unsafe { ffi::liq_set_min_posterization(&mut *self.handle, value) }
    }

    /// Returns number of bits of precision truncated
    #[inline]
    pub fn min_posterization(&mut self) -> i32 {
        unsafe { ffi::liq_get_min_posterization(&*self.handle) }
    }

    /// Range 0-100, roughly like JPEG.
    ///
    /// If minimum quality can't be met, quantization will fail.
    ///
    /// Default is min 0, max 100.
    #[inline]
    pub fn set_quality(&mut self, min: u32, max: u32) -> liq_error {
        unsafe { ffi::liq_set_quality(&mut *self.handle, min as c_int, max as c_int) }
    }

    /// Reads values set with `set_quality`
    #[inline]
    pub fn quality(&mut self) -> (u32, u32) {
        unsafe {
            (ffi::liq_get_min_quality(&*self.handle) as u32,
             ffi::liq_get_max_quality(&*self.handle) as u32)
        }
    }

    /// 1-10.
    ///
    /// Faster speeds generate images of lower quality, but may be useful
    /// for real-time generation of images.
    #[inline]
    pub fn set_speed(&mut self, value: i32) -> liq_error {
        unsafe { ffi::liq_set_speed(&mut *self.handle, value) }
    }

    /// Move transparent color to the last entry in the palette
    ///
    /// This is less efficient for PNG, but required by some broken software
    #[inline]
    pub fn set_last_index_transparent(&mut self, value: bool) {
        unsafe { ffi::liq_set_last_index_transparent(&mut *self.handle, value as c_int) }
    }

    /// Return currently set speed/quality trade-off setting
    #[inline(always)]
    #[must_use]
    pub fn speed(&mut self) -> i32 {
        unsafe { ffi::liq_get_speed(&*self.handle) }
    }

    /// Return max number of colors set
    #[inline(always)]
    #[must_use]
    pub fn max_colors(&mut self) -> i32 {
        unsafe { ffi::liq_get_max_colors(&*self.handle) }
    }

    /// Describe dimensions of a slice of RGBA pixels
    ///
    /// Use 0.0 for gamma if the image is sRGB (most images are).
    #[inline]
    pub fn new_image<'a>(&self, bitmap: &'a [RGBA], width: usize, height: usize, gamma: f64) -> Result<Image<'a>, liq_error> {
        Image::new(self, bitmap, width, height, gamma)
    }

    /// Stride is in pixels. Allows defining regions of larger images or images with padding without copying.
    #[inline]
    pub fn new_image_stride<'a>(&self, bitmap: &'a [RGBA], width: usize, height: usize, stride: usize, gamma: f64) -> Result<Image<'a>, liq_error> {
        Image::new_stride(self, bitmap, width, height, stride, gamma)
    }

    /// Like `new_image_stride`, but makes a copy of the pixels
    #[inline]
    pub fn new_image_stride_copy(&self, bitmap: &[RGBA], width: usize, height: usize, stride: usize, gamma: f64) -> Result<Image<'static>, liq_error> {
        Image::new_stride_copy(self, bitmap, width, height, stride, gamma)
    }

    /// Create new histogram
    ///
    /// Use to make one palette suitable for many images
    #[inline(always)]
    #[must_use]
    pub fn new_histogram(&self) -> Histogram<'_> {
        Histogram::new(&self)
    }

    /// Generate palette for the image
    pub fn quantize(&mut self, image: &Image<'_>) -> Result<QuantizationResult, liq_error> {
        unsafe {
            let mut h = ptr::null_mut();
            match ffi::liq_image_quantize(&*image.handle, &*self.handle, &mut h) {
                liq_error::LIQ_OK if !h.is_null() => Ok(QuantizationResult { handle: h }),
                err => Err(err),
            }
        }
    }
}

/// Start here: creates new handle for library configuration
#[inline(always)]
#[must_use]
pub fn new() -> Attributes {
    Attributes::new()
}

impl<'a> Histogram<'a> {
    /// Creates histogram object that will be used to collect color statistics from multiple images.
    ///
    /// All options should be set on `attr` before the histogram object is created. Options changed later may not have effect.
    #[inline]
    #[must_use]
    pub fn new(attr: &'a Attributes) -> Self {
        Histogram {
            attr,
            handle: unsafe { ffi::liq_histogram_create(&*attr.handle) },
        }
    }

    /// "Learns" colors from the image, which will be later used to generate the palette.
    ///
    /// Fixed colors added to the image are also added to the histogram. If total number of fixed colors exceeds 256, this function will fail with `LIQ_BUFFER_TOO_SMALL`.
    #[inline]
    pub fn add_image(&mut self, image: &mut Image<'_>) -> liq_error {
        unsafe { ffi::liq_histogram_add_image(&mut *self.handle, &*self.attr.handle, &mut *image.handle) }
    }

    /// Alternative to `add_image()`. Intead of counting colors in an image, it directly takes an array of colors and their counts.
    ///
    /// This function is only useful if you already have a histogram of the image from another source.
    #[inline]
    pub fn add_colors(&mut self, colors: &[HistogramEntry], gamma: f64) -> liq_error {
        unsafe {
            ffi::liq_histogram_add_colors(&mut *self.handle, &*self.attr.handle, colors.as_ptr(), colors.len() as c_int, gamma)
        }
    }

    /// Generate palette for all images/colors added to the histogram.
    ///
    /// Palette generated using this function won't be improved during remapping.
    /// If you're generating palette for only one image, it's better not to use the `Histogram`.
    #[inline]
    pub fn quantize(&mut self) -> Result<QuantizationResult, liq_error> {
        unsafe {
            let mut h = ptr::null_mut();
            match ffi::liq_histogram_quantize(&*self.handle, &*self.attr.handle, &mut h) {
                liq_error::LIQ_OK if !h.is_null() => Ok(QuantizationResult { handle: h }),
                err => Err(err),
            }
        }
    }
}

/// Generate image row on the fly
///
/// `output_row` is an array `width` RGBA elements wide.
/// `y` is the row (0-indexed) to write to the `output_row`
/// `user_data` is the data given to `Image::new_unsafe_fn()`
pub type ConvertRowUnsafeFn<UserData> = unsafe extern "C" fn(output_row: *mut Color, y: c_int, width: c_int, user_data: *mut UserData);

impl<'bitmap> Image<'bitmap> {
    /// Describe dimensions of a slice of RGBA pixels.
    ///
    /// `bitmap` must be either `&[u8]` or a slice with one element per pixel (`&[RGBA]`).
    ///
    /// Use `0.` for gamma if the image is sRGB (most images are).
    #[inline(always)]
    pub fn new(attr: &Attributes, bitmap: &'bitmap [RGBA], width: usize, height: usize, gamma: f64) -> Result<Self, liq_error> {
        Self::new_stride(attr, bitmap, width, height, width, gamma)
    }

    /// Generate rows on demand using a callback function.
    ///
    /// The callback function must be cheap (e.g. just byte-swap pixels).
    /// It will be called multiple times per row. May be called in any order from any thread.
    ///
    /// The user data must be compatible with a primitive pointer
    /// (i.e. not a slice, not a Trait object. `Box` it if you must).
    #[inline]
    pub fn new_unsafe_fn<CustomData: Send + Sync + 'bitmap>(attr: &Attributes, convert_row_fn: ConvertRowUnsafeFn<CustomData>, user_data: *mut CustomData, width: usize, height: usize, gamma: f64) -> Result<Self, liq_error> {
        unsafe {
            match ffi::liq_image_create_custom(&*attr.handle, mem::transmute(convert_row_fn), user_data.cast(), width as c_int, height as c_int, gamma) {
                handle if !handle.is_null() => Ok(Image { handle, _marker: PhantomData }),
                _ => Err(LIQ_INVALID_POINTER),
            }
        }
    }

    /// Stride is in pixels. Allows defining regions of larger images or images with padding without copying.
    #[inline(always)]
    pub fn new_stride(attr: &Attributes, bitmap: &'bitmap [RGBA], width: usize, height: usize, stride: usize, gamma: f64) -> Result<Self, liq_error> {
        // Type definition preserves the lifetime, so it's not unsafe
        unsafe { Self::new_stride_internal(attr, bitmap, width, height, stride, gamma, false) }
    }

    /// Create new image by copying `bitmap` to an internal buffer, so that it makes a self-contained type.
    #[inline(always)]
    pub fn new_stride_copy(attr: &Attributes, bitmap: &[RGBA], width: usize, height: usize, stride: usize, gamma: f64) -> Result<Image<'static>, liq_error> {
        // copy guarantees the image doesn't reference the bitmap any more
        unsafe { Self::new_stride_internal(attr, bitmap, width, height, stride, gamma, true) }
    }

    unsafe fn new_stride_internal<'varies>(attr: &Attributes, bitmap: &[RGBA], width: usize, height: usize, stride: usize, gamma: f64, copy: bool) -> Result<Image<'varies>, liq_error> {
        if bitmap.len() < (stride * height + width - stride) {
            eprintln!("Buffer length is {} bytes, which is not enough for {}×{}×4 RGBA bytes", bitmap.len()*4, stride, height);
            return Err(LIQ_BUFFER_TOO_SMALL);
        }
        let (bitmap, ownership) = if copy {
            let copied = (attr.malloc)(4 * bitmap.len()) as *mut RGBA;
            ptr::copy_nonoverlapping(bitmap.as_ptr(), copied, bitmap.len());
            (copied as *const _, ffi::liq_ownership::LIQ_OWN_ROWS | ffi::liq_ownership::LIQ_OWN_PIXELS)
        } else {
            (bitmap.as_ptr(), ffi::liq_ownership::LIQ_OWN_ROWS)
        };
        let rows = Self::malloc_image_rows(bitmap, stride, height, attr.malloc);
        let h = ffi::liq_image_create_rgba_rows(&*attr.handle, rows, width as c_int, height as c_int, gamma);
        if h.is_null() {
            (attr.free)(rows.cast());
            return Err(LIQ_INVALID_POINTER);
        }
        let img = Image {
            handle: h,
            _marker: PhantomData,
        };
        match ffi::liq_image_set_memory_ownership(&*h, ownership) {
            LIQ_OK => Ok(img),
            err => {
                drop(img);
                (attr.free)(rows.cast());
                Err(err)
            },
        }
    }

    /// For arbitrary stride libimagequant requires rows. It's most convenient if they're allocated using libc,
    /// so they can be owned and freed automatically by the C library.
    unsafe fn malloc_image_rows(bitmap: *const RGBA, stride: usize, height: usize, malloc: MallocUnsafeFn) -> *mut *const u8 {
        let mut byte_ptr = bitmap as *const u8;
        let stride_bytes = stride * 4;
        let rows = malloc(mem::size_of::<*const u8>() * height) as *mut *const u8;
        for y in 0..height {
            *rows.add(y) = byte_ptr;
            byte_ptr = byte_ptr.add(stride_bytes);
        }
        rows
    }

    /// Width of the image in pixels
    #[inline]
    #[must_use]
    pub fn width(&self) -> usize {
        unsafe { ffi::liq_image_get_width(&*self.handle) as usize }
    }

    /// Height of the image in pixels
    #[inline]
    #[must_use]
    pub fn height(&self) -> usize {
        unsafe { ffi::liq_image_get_height(&*self.handle) as usize }
    }

    /// Reserves a color in the output palette created from this image. It behaves as if the given color was used in the image and was very important.
    ///
    /// RGB values of liq_color are assumed to have the same gamma as the image.
    ///
    /// It must be called before the image is quantized.
    ///
    /// Returns error if more than 256 colors are added. If image is quantized to fewer colors than the number of fixed colors added, then excess fixed colors will be ignored.
    #[inline]
    pub fn add_fixed_color(&mut self, color: ffi::liq_color) -> liq_error {
        unsafe { ffi::liq_image_add_fixed_color(&mut *self.handle, color) }
    }

    /// Remap pixels assuming they will be displayed on this background.
    ///
    /// Pixels that match the background color will be made transparent if there's a fully transparent color available in the palette.
    ///
    /// The background image's pixels must outlive this image
    #[inline]
    pub fn set_background<'own, 'bg: 'own>(&'own mut self, background: Image<'bg>) -> Result<(), liq_error> {
        unsafe {
            ffi::liq_image_set_background(&mut *self.handle, background.into_raw()).ok()
        }
    }

    /// Set which pixels are more important (and more likely to get a palette entry)
    ///
    /// The map must be `width`×`height` pixels large. Higher numbers = more important.
    #[inline]
    pub fn set_importance_map(&mut self, map: &[u8]) -> Result<(), liq_error> {
        unsafe {
            ffi::liq_image_set_importance_map(&mut *self.handle, map.as_ptr() as *mut _, map.len(), ffi::liq_ownership::LIQ_COPY_PIXELS).ok()
        }
    }

    #[inline]
    fn into_raw(mut self) -> *mut ffi::liq_image {
        let handle = self.handle;
        self.handle = ptr::null_mut();
        handle
    }
}

impl QuantizationResult {
    /// Set to 1.0 to get nice smooth image
    #[inline]
    pub fn set_dithering_level(&mut self, value: f32) -> liq_error {
        unsafe { ffi::liq_set_dithering_level(&mut *self.handle, value) }
    }

    /// The default is sRGB gamma (~1/2.2)
    #[inline]
    pub fn set_output_gamma(&mut self, value: f64) -> liq_error {
        unsafe { ffi::liq_set_output_gamma(&mut *self.handle, value) }
    }

    /// Approximate gamma correction value used for the output
    ///
    /// Colors are converted from input gamma to this gamma
    #[inline]
    #[must_use]
    pub fn output_gamma(&mut self) -> f64 {
        unsafe { ffi::liq_get_output_gamma(&*self.handle) }
    }

    /// Number 0-100 guessing how nice the input image will look if remapped to this palette
    #[inline]
    #[must_use]
    pub fn quantization_quality(&self) -> i32 {
        unsafe { ffi::liq_get_quantization_quality(&*self.handle) as i32 }
    }

    /// Approximate mean square error of the palette
    #[inline]
    #[must_use]
    pub fn quantization_error(&self) -> Option<f64> {
        match unsafe { ffi::liq_get_quantization_error(&*self.handle) } {
            x if x < 0. => None,
            x => Some(x),
        }
    }

    /// Final palette
    ///
    /// It's slighly better if you get palette from the `remapped()` call instead
    #[must_use]
    pub fn palette(&mut self) -> Vec<Color> {
        let pal = self.palette_ref();
        let mut out: Vec<Color> = FallibleVec::try_with_capacity(pal.len()).unwrap();
        out.extend_from_slice(pal);
        out
    }

    /// Final palette (as a temporary slice)
    ///
    /// It's slighly better if you get palette from the `remapped()` call instead
    ///
    /// Use when ownership of the palette colors is not needed
    #[inline]
    pub fn palette_ref(&mut self) -> &[Color] {
        unsafe {
            let pal = &*ffi::liq_get_palette(&mut *self.handle);
            std::slice::from_raw_parts(pal.entries.as_ptr(), (pal.count as usize).min(pal.entries.len()))
        }
    }

    /// Remap image into a `Vec`
    ///
    /// Returns the palette and a 1-byte-per-pixel uncompressed bitmap
    pub fn remapped(&mut self, image: &mut Image<'_>) -> Result<(Vec<Color>, Vec<u8>), liq_error> {
        let len = image.width() * image.height();
        // Capacity is essential here, as it creates uninitialized buffer
        unsafe {
            let mut buf: Vec<u8> = FallibleVec::try_with_capacity(len).map_err(|_| liq_error::LIQ_OUT_OF_MEMORY)?;
            let uninit_slice = std::slice::from_raw_parts_mut(buf.as_ptr() as *mut MaybeUninit<u8>, buf.capacity());
            self.remap_into(image, uninit_slice)?;
            buf.set_len(uninit_slice.len());
            Ok((self.palette(), buf))
        }
    }

    /// Remap image into an existing buffer.
    ///
    /// This is a low-level call for use when existing memory has to be reused. Use `remapped()` if possible.
    ///
    /// Writes 1-byte-per-pixel uncompressed bitmap into the pre-allocated buffer.
    ///
    /// You should call `palette()` or `palette_ref()` _after_ this call, but not before it,
    /// because remapping changes the palette.
    #[inline]
    pub fn remap_into(&mut self, image: &mut Image<'_>, output_buf: &mut [MaybeUninit<u8>]) -> Result<(), liq_error> {
        unsafe {
            match ffi::liq_write_remapped_image(&mut *self.handle, &mut *image.handle, output_buf.as_mut_ptr().cast(), output_buf.len()) {
                LIQ_OK => Ok(()),
                err => Err(err),
            }
        }
    }
}

impl fmt::Debug for QuantizationResult {
    #[cold]
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "QuantizationResult(q={})", self.quantization_quality())
    }
}

unsafe impl Send for Attributes {}
unsafe impl Send for QuantizationResult {}
unsafe impl<'bitmap> Send for Image<'bitmap> {}
unsafe impl<'a> Send for Histogram<'a> {}

#[test]
fn copy_img() {
    let tmp = vec![RGBA::new(1,2,3,4); 10*100];
    let liq = Attributes::new();
    let _ = liq.new_image_stride_copy(&tmp, 10, 100, 10, 0.).unwrap();
}

#[test]
fn takes_rgba() {
    let liq = Attributes::new();

    use rgb::RGBA8 as RGBA;
    let img = vec![RGBA {r:0, g:0, b:0, a:0}; 8];


    liq.new_image(&img, 1, 1, 0.0).unwrap();
    liq.new_image(&img, 4, 2, 0.0).unwrap();
    liq.new_image(&img, 8, 1, 0.0).unwrap();
    assert!(liq.new_image(&img, 9, 1, 0.0).is_err());
    assert!(liq.new_image(&img, 4, 3, 0.0).is_err());
}

#[test]
fn histogram() {
    let attr = Attributes::new();
    let mut hist = attr.new_histogram();

    let bitmap1 = vec![RGBA {r:0, g:0, b:0, a:0}; 1];
    let mut image1 = attr.new_image(&bitmap1[..], 1, 1, 0.0).unwrap();
    hist.add_image(&mut image1);

    let bitmap2 = vec![RGBA {r:255, g:255, b:255, a:255}; 1];
    let mut image2 = attr.new_image(&bitmap2[..], 1, 1, 0.0).unwrap();
    hist.add_image(&mut image2);

    hist.add_colors(&[HistogramEntry{
        color: Color::new(255,128,255,128),
        count: 10,
    }], 0.0);

    let mut res = hist.quantize().unwrap();
    let pal = res.palette();
    assert_eq!(3, pal.len());
}

#[test]
fn poke_it() {
    let width = 10usize;
    let height = 10usize;
    let mut fakebitmap = vec![RGBA::new(255,255,255,255); width*height];

    fakebitmap[0].r = 0x55;
    fakebitmap[0].g = 0x66;
    fakebitmap[0].b = 0x77;

    // Configure the library
    let mut liq = Attributes::new();
    liq.set_speed(5);
    liq.set_quality(70, 99);
    liq.set_min_posterization(1);
    assert_eq!(1, liq.min_posterization());
    liq.set_min_posterization(0);

    // Describe the bitmap
    let ref mut img = liq.new_image(&fakebitmap[..], width, height, 0.0).unwrap();

    // The magic happens in quantize()
    let mut res = match liq.quantize(img) {
        Ok(res) => res,
        Err(err) => panic!("Quantization failed, because: {:?}", err),
    };

    // Enable dithering for subsequent remappings
    res.set_dithering_level(1.0);

    // You can reuse the result to generate several images with the same palette
    let (palette, pixels) = res.remapped(img).unwrap();

    assert_eq!(width * height, pixels.len());
    assert_eq!(100, res.quantization_quality());
    assert_eq!(Color { r: 255, g: 255, b: 255, a: 255 }, palette[0]);
    assert_eq!(Color { r: 0x55, g: 0x66, b: 0x77, a: 255 }, palette[1]);
}

#[test]
fn set_importance_map() {
    use crate::ffi::liq_color as RGBA;
    let mut liq = new();
    let bitmap = &[RGBA::new(255, 0, 0, 255), RGBA::new(0u8, 0, 255, 255)];
    let ref mut img = liq.new_image(&bitmap[..], 2, 1, 0.).unwrap();
    let map = &[255, 0];
    img.set_importance_map(map).unwrap();
    let mut res = liq.quantize(img).unwrap();
    let pal = res.palette();
    assert_eq!(1, pal.len());
    assert_eq!(bitmap[0], pal[0]);
}

#[test]
fn thread() {
    let liq = Attributes::new();
    std::thread::spawn(move || {
        let b = vec![RGBA::new(0,0,0,0);1];
        liq.new_image(&b, 1, 1, 0.).unwrap();
    }).join().unwrap();
}

#[test]
fn callback_test() {
    let mut called = 0;
    let mut res = {
        let mut a = new();
        unsafe extern "C" fn get_row(output_row: *mut Color, y: c_int, width: c_int, user_data: *mut i32) {
            assert!(y >= 0 && y < 5);
            assert_eq!(123, width);
            for i in 0..width as isize {
                let n = i as u8;
                *output_row.offset(i as isize) = Color::new(n,n,n,n);
            }
            *user_data += 1;
        }
        let mut img = Image::new_unsafe_fn(&a, get_row, &mut called, 123, 5, 0.).unwrap();
        a.quantize(&mut img).unwrap()
    };
    assert!(called > 5 && called < 50);
    assert_eq!(123, res.palette().len());
}

#[test]
fn custom_allocator_test() {
    // SAFETY: This is all in one thread.
    static mut ALLOC_COUNTR: usize = 0;
    static mut FREE_COUNTR: usize = 0;

    unsafe extern "C" fn test_malloc(size: usize) -> *mut c_void {
        ALLOC_COUNTR += 1;
        libc::malloc(size)
    }

    unsafe extern "C" fn test_free(ptr: *mut c_void) {
        FREE_COUNTR += 1;
        libc::free(ptr)
    }

    let liq = unsafe { Attributes::with_allocator(test_malloc, test_free) };
    assert_eq!(unsafe { ALLOC_COUNTR }, 1);
    assert_eq!(unsafe { FREE_COUNTR }, 0);

    let liq2 = liq.clone();
    assert_eq!(liq.malloc, liq2.malloc);
    assert_eq!(liq.free, liq2.free);

    drop(liq);
    assert_eq!(unsafe { ALLOC_COUNTR }, 2);
    assert_eq!(unsafe { FREE_COUNTR }, 1);

    drop(liq2);
    assert_eq!(unsafe { ALLOC_COUNTR }, 2);
    assert_eq!(unsafe { FREE_COUNTR }, 2);
}
