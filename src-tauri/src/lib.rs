use crate::process::Process;

mod process;

#[tauri::command]
fn get_foreground_process() -> Result<Process, ()> {
    process::get_foreground_process()
}

#[tauri::command]
fn suspend_process(pid: u32) -> Result<(), ()> {
    process::suspend_process(pid)
}

#[tauri::command]
fn resume_process(pid: u32) -> Result<(), ()> {
    process::resume_process(pid)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            get_foreground_process,
            suspend_process,
            resume_process,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
