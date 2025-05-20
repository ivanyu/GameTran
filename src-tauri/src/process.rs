use std::ffi::c_void;
use scopeguard::defer;
use serde::Serialize;
use windows::Win32::Foundation::{CloseHandle, HWND};
use windows::Win32::Graphics::Gdi::{MonitorFromWindow, MONITOR_DEFAULTTONULL};
use windows::Win32::System::Threading::{OpenProcess, PROCESS_ALL_ACCESS};
use windows::Win32::UI::HiDpi::{GetDpiForMonitor, SetThreadDpiAwarenessContext, DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE, MDT_DEFAULT};
use windows::Win32::UI::WindowsAndMessaging::{GetForegroundWindow, GetWindowThreadProcessId, SetForegroundWindow};
use windows_native::ntpsapi::{NtResumeProcess, NtSuspendProcess};
use log::error;

#[derive(Serialize, Debug)]
pub(crate) struct Process {
    pub(crate) pid: u32,
    pub(crate) hwnd: isize,
    pub(crate) scale_factor: f32,
}

pub(crate) fn get_foreground_process() -> Result<Process, ()> {
    let hwnd = unsafe { GetForegroundWindow() };
    if hwnd.is_invalid() {
        error!("Error getting foreground window");
        return Err(());
    }

    let mut pid: u32 = 0;
    unsafe { GetWindowThreadProcessId(hwnd, Some(&mut pid)) };
    if pid == 0 {
        error!("Error getting window process id");
        return Err(());
    }

    Ok(Process {
        pid,
        hwnd: hwnd.0 as isize,
        scale_factor: get_scale_factor(hwnd)?
    })
}

fn get_scale_factor(hwnd: HWND) -> Result<f32, ()> {
    let prev_dpi_awareness_context = unsafe {
        SetThreadDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE)
    };
    if prev_dpi_awareness_context.is_invalid() {
        error!("Error setting DPI awareness context");
        return Err(());
    }

    defer! {
        if unsafe { SetThreadDpiAwarenessContext(prev_dpi_awareness_context) }.is_invalid() {
            error!("Error restoring DPI awareness context");
        }
    }

    let hmonitor = unsafe { MonitorFromWindow(hwnd, MONITOR_DEFAULTTONULL) };
    if hmonitor.is_invalid() {
        error!("Error getting window monitor");
        return Err(());
    }

    let mut dpi_x: u32 = 0;
    let mut dpi_y: u32 = 0;
    unsafe { GetDpiForMonitor(hmonitor, MDT_DEFAULT, &mut dpi_x, &mut dpi_y) }.map_err(|e| {
        error!("Error getting DPI: {}", e);
        ()
    })?;

    Ok((dpi_y as f32) / 96.0)
}

pub(crate) fn suspend_process(pid: u32) -> Result<(), ()> {
    if let Ok(handle) = unsafe { OpenProcess(PROCESS_ALL_ACCESS, false, pid) } {
        defer! {
            let _ = unsafe { CloseHandle(handle) }
            .map_err(|e| {error!("{}", e)});
        }

        let result = unsafe { NtSuspendProcess(handle) };
        if result.is_ok() {
            Ok(())
        } else {
            error!("Error suspending process");
            Err(())
        }
    } else {
        error!("Error opening process");
        Err(())
    }
}

pub(crate) fn resume_process(pid: u32) -> Result<(), ()> {
    if let Ok(handle) = unsafe { OpenProcess(PROCESS_ALL_ACCESS, false, pid) } {
        defer! {
            let _ = unsafe { CloseHandle(handle) }
            .map_err(|e| {error!("{}", e)});
        }

        let result = unsafe { NtResumeProcess(handle) };
        if result.is_ok() {
            Ok(())
        } else {
            error!("Error resuming process");
            Err(())
        }
    } else {
        error!("Error opening process");
        Err(())
    }
}

pub(crate) fn bring_window_to_foreground(hwnd: isize) -> Result<(), ()> {
    let hwnd = HWND(hwnd as *mut c_void);
    if unsafe { SetForegroundWindow(hwnd) }.as_bool() {
        Ok(())
    } else {
        error!("Error setting foreground window");
        Err(())
    }
}
