use base64::prelude::BASE64_STANDARD;
use std::io::Cursor;
use base64::Engine;
use image::{load_from_memory_with_format, DynamicImage, ImageFormat};
use image::imageops::FilterType;
use log::error;

pub(crate) fn prepare_screenshot_for_ocr(bytes_png: &[u8], target_height: u32) -> Result<String, ()> {
    let image = load_from_memory_with_format(bytes_png, ImageFormat::Png).map_err(|e| {
        error!("Error reading image: {:?}", e);
        ()
    })?;
    let screenshot = DynamicImage::from(image.to_rgb8());

    let scale_factor = screenshot.height() as f32 / (target_height as f32);

    let scaled_width = (screenshot.width() as f32 / scale_factor) as u32;
    let scaled_height = (screenshot.height() as f32 / scale_factor) as u32;

    // TODO consider worse but faster filters
    // TODO it should also be faster in the release mode https://github.com/image-rs/image/issues/1424
    let scaled_image = screenshot.resize(scaled_width, scaled_height, FilterType::Gaussian);

    let mut bytes_jpeg: Vec<u8> = Vec::new();
    let mut cursor = Cursor::new(&mut bytes_jpeg);
    scaled_image
        .write_to(&mut cursor, ImageFormat::Jpeg)
        .map_err(|e| {
            error!("Error saving as Jpeg: {:?}", e);
            ()
        })?;
    Ok(BASE64_STANDARD.encode(bytes_jpeg))
}
