use log::error;
use tauri::ipc::CapabilityBuilder;
use tauri::Manager;

#[cfg(target_os = "windows")]
use crate::process::Process;

#[cfg(target_os = "windows")]
mod process;
#[cfg(target_os = "windows")]
mod screenshot;
mod ocr;

#[cfg(target_os = "windows")]
#[tauri::command]
fn get_foreground_process() -> Result<Process, ()> {
    process::get_foreground_process()
}

#[cfg(target_os = "windows")]
#[tauri::command]
fn suspend_process(pid: u32) -> Result<(), ()> {
    process::suspend_process(pid)
}

#[cfg(target_os = "windows")]
#[tauri::command]
fn take_screenshot(hwnd: isize) -> Result<Vec<u8>, ()> {
    screenshot::take_screenshot(hwnd)
}

#[cfg(target_os = "windows")]
#[tauri::command]
fn resume_process(pid: u32) -> Result<(), ()> {
    process::resume_process(pid)
}

#[cfg(target_os = "windows")]
#[tauri::command]
fn bring_window_to_foreground(hwnd: isize) -> Result<(), ()> {
    process::bring_window_to_foreground(hwnd)
}

#[tauri::command]
fn prepare_screenshot_for_ocr(screenshot_png: Vec<u8>, target_height: u32) -> Result<String, ()> {
    ocr::prepare_screenshot_for_ocr(screenshot_png.as_slice(), target_height)
}

#[tauri::command]
fn dev_features() -> Result<Vec<String>, ()> {
    #[cfg(feature = "mock_process_and_screenshot")]
    {
        Ok(vec![String::from("mock_process_and_screenshot")])
    }
    #[cfg(not(feature = "mock_process_and_screenshot"))]
    {
        Ok(vec![])
    }
}

#[cfg(feature = "mock_process_and_screenshot")]
#[tauri::command]
fn dev_get_path(file: String) -> Result<String, ()> {
    let cd = std::env::current_dir().map_err(|e| {
        error!("Failed to get current working directory: {}", e);
        ()
    })?;
    let final_path = cd
        .join("..")
        .canonicalize()
        .map_err(|e| {
            error!("Failed to canonicalize: {}", e);
            ()
        })?
        .join(file);
    Ok(final_path.to_str().unwrap().to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            #[cfg(target_os = "windows")]
            get_foreground_process,
            #[cfg(target_os = "windows")]
            suspend_process,
            #[cfg(target_os = "windows")]
            take_screenshot,
            #[cfg(target_os = "windows")]
            resume_process,
            #[cfg(target_os = "windows")]
            bring_window_to_foreground,
            prepare_screenshot_for_ocr,
            dev_features,
            #[cfg(feature = "mock_process_and_screenshot")]
            dev_get_path,
        ])
        .setup(|#[allow(unused_variables)] app| {
            #[cfg(feature = "mock_process_and_screenshot")]
            {
                app.add_capability(
                    CapabilityBuilder::new("dev-main-read-resources")
                        .window("main")
                        .permission_scoped("fs:allow-resource-read-recursive", vec!["/**"], vec![]),
                )
                .unwrap();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
