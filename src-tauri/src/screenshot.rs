use image::{DynamicImage, ImageFormat, RgbaImage};
use log::error;
use std::io::Cursor;
use win_screenshot::capture::Using::PrintWindow;
use win_screenshot::capture::{capture_window_ex, Area};

pub(crate) fn take_screenshot(hwnd: isize) -> Result<Vec<u8>, ()> {
    let buf = capture_window_ex(hwnd, PrintWindow, Area::ClientOnly, None, None).map_err(|e| {
        error!("Error capturing: {:?}", e);
        ()
    })?;

    if let Some(img_buf) = RgbaImage::from_raw(buf.width, buf.height, buf.pixels) {
        let image = DynamicImage::ImageRgba8(img_buf);
        let mut bytes_png: Vec<u8> = Vec::new();
        image
            .write_to(&mut Cursor::new(&mut bytes_png), image::ImageFormat::Png)
            .map_err(|e| {
                error!("Error saving as PNG: {:?}", e);
                ()
            })?;
        Ok(bytes_png)
    } else {
        error!("Error creating image");
        Err(())
    }
}
