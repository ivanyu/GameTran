import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import {action, makeObservable, observable} from "mobx";
import {register, ShortcutEvent, unregister} from "@tauri-apps/plugin-global-shortcut";
import {debug, error, warn} from "@tauri-apps/plugin-log";
import {getCurrentWindow, Window} from "@tauri-apps/api/window";
import {observer} from "mobx-react-lite";
import {invoke} from "@tauri-apps/api/core";
import {TrayIcon} from '@tauri-apps/api/tray';
import {defaultWindowIcon} from "@tauri-apps/api/app";
import {Menu} from '@tauri-apps/api/menu';
import {exit} from '@tauri-apps/plugin-process';
import {open, readTextFile} from '@tauri-apps/plugin-fs';
import Settings from "./settings.ts";
import getOcr, {OcrResponse} from "./ocr.ts";

// Load developer features.
const DeveloperFeatures = {
    mockProcessAndScreenshot: false,
};
{
    const dev_features = await invoke<string[]>("dev_features");
    if (dev_features.includes('mock_process_and_screenshot')) {
        DeveloperFeatures.mockProcessAndScreenshot = true;
        debug('DeveloperFeatures.mockProcessAndScreenshot: true');
    }
}

const TrayIconId = 'trayIconId';
const Shortcut = 'Alt+P';
const SettingsWindowID = 'settings';

const settings = new Settings();
try {
    await settings.init();
} catch (e) {
    await error(`Error initializing settings: ${e}`);
    throw e;
}

// Setup windows.
const mainWindow = getCurrentWindow();

await mainWindow.onCloseRequested((e) => {
    e.preventDefault();
    mainWindow.hide();
});

const settingsWindow = await Window.getByLabel(SettingsWindowID);
if (!settingsWindow) {
    await error('Settings window not found');
    await exit(1);
} else {
    await settingsWindow.onCloseRequested((e) => {
        e.preventDefault();
        settingsWindow.hide();
    });
}

class State {
    active: boolean;
    process?: Process;
    screenshotPng?: ArrayBuffer;
    screenshotUrl?: string;
    ocr?: OcrResponse;

    constructor() {
        makeObservable(this, {
            active: observable,
            process: observable,
            screenshotUrl: observable,
            setScreenshot: action,
            clear: action,
        });
    }

    setScreenshot(png: ArrayBuffer) {
        this.screenshotPng = new Uint8Array(png);
        const blob = new Blob([new Uint8Array(png)], {type: 'image/png'});
        if (this.screenshotUrl) {
            URL.revokeObjectURL(this.screenshotUrl);
        }
        this.screenshotUrl = URL.createObjectURL(blob);
    }

    setOcr(ocr: OcrResponse | undefined) {
        this.ocr = ocr;
        error(`OCR: ${JSON.stringify(ocr)}`);
    }

    clear() {
        this.active = false;
        this.process = undefined;
        if (this.screenshotUrl) {
            URL.revokeObjectURL(this.screenshotUrl);
        }
        this.screenshotPng = undefined;
        this.screenshotUrl = undefined;
    }
}

type Process = {
    pid: number;
    hwnd: number;
    scale_factor: number;
};

const state = observable<State>(new State());

const AppWrapper = observer(({state}: {state: State}) => {
    return state.active && state.screenshotUrl
        ? <App screenshotUrl={state.screenshotUrl!}/>
        : null
});
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <AppWrapper state={state} />
    </React.StrictMode>,
);

async function getForegroundProcess(): Promise<Process> {
    if (DeveloperFeatures.mockProcessAndScreenshot) {
        await debug("Getting foreground process (mock)");
        return  {pid: 0, hwnd: 0, scale_factor: 1};
    } else {
        await debug("Getting foreground process");
        return await invoke<Process>("get_foreground_process");
    }
}

async function suspendProcess(pid: number) {
    if (DeveloperFeatures.mockProcessAndScreenshot) {
        await debug(`Suspending foreground process ${pid} (mock)`);
    } else {
        await debug(`Suspending foreground process ${pid}`);
        await invoke("suspend_process", {pid});
    }
}

async function resumeProcess(pid: number) {
    // Don't "optimize" hiding and showing here: the chance of an error in resuming is small and that's OK to pay for it with a bit of flickering
    // to allow the window hide in the normal circumstances faster.
    if (DeveloperFeatures.mockProcessAndScreenshot) {
        await debug(`Resuming foreground process ${pid} (mock)`);
    } else {
        await debug(`Resuming foreground process ${pid}`);
        await invoke("resume_process", {pid});
    }
}

async function takeScreenshot(hwnd: number): Promise<ArrayBuffer> {
    if (DeveloperFeatures.mockProcessAndScreenshot) {
        await debug(`Taking screenshot of ${hwnd} (mock)`);

        const configContent = await readTextFile(await invoke("dev_mock_screenshot_file", {file: "config.txt"}));
        const lines = configContent.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#'));  // filter out empty lines and comments
        
        if (lines.length === 0) {
            throw new Error("No valid screenshot files found in config");
        }

        const randomIndex = Math.floor(Math.random() * lines.length);
        const selectedFile = lines[randomIndex];

        const screenshotPath = await invoke<string>("dev_mock_screenshot_file", {file: selectedFile});
        const file = await open(screenshotPath);
        try {
            const fileStat = await file.stat();
            const buf = new Uint8Array(fileStat.size);
            await file.read(buf);
            return buf.buffer;
        } finally {
            await file.close();
        }
    } else {
        await debug(`Taking screenshot of ${hwnd}`);
        return await invoke<ArrayBuffer>('take_screenshot', {hwnd});
    }
}

async function bringWindowToForeground(hwnd: number) {
    if (DeveloperFeatures.mockProcessAndScreenshot) {
        await debug(`Bringing ${hwnd} to foreground (mock)`);
    } else {
        return await invoke("bring_window_to_foreground", {hwnd});
    }
}

unregister(Shortcut);
register(Shortcut, async (event: ShortcutEvent) => {
    if (event.state === "Pressed") {
        debug('Shortcut pressed');

        if (state.active) {
            if (!state.process) {
                warn(`Session is active, but no process`);
                return;
            }

            await mainWindow.hide();

            // Don't "optimize" hiding and showing here: the chance of an error in resuming is small and that's OK to pay for it with a bit of flickering
            // to allow the window hide in the normal circumstances faster.
            const pid = state.process.pid;
            debug(`Resuming foreground process ${pid}`);
            let resumedSuccessfully = false;
            try {
                await resumeProcess(pid);
                resumedSuccessfully = true;
            } catch (e) {
                let message;
                if (e instanceof Error) {
                    message = `Error resuming process ${pid}: ${e.message}`;
                } else {
                    message = `Error resuming process ${pid}: ${JSON.stringify(e)}`;
                }
                await error(message);
                await mainWindow.show();
                alert(message)
                await mainWindow.hide();
            }

            if (resumedSuccessfully) {
                debug("Restoring foreground window");
                try {
                    await bringWindowToForeground(state.process.hwnd)
                } catch (e) {
                    let message;
                    if (e instanceof Error) {
                        message = `Error restoring foreground window: ${e.message}`;
                    } else {
                        message = `Error restoring foreground window: ${JSON.stringify(e)}`;
                    }
                    await error(message);
                    await getCurrentWindow().show();
                    alert(message)
                    await getCurrentWindow().hide();
                }
            }

            state.active = false;
            state.process = undefined;
        } else {
            try {
                state.process = await getForegroundProcess();
            } catch (e) {
                let message;
                if (e instanceof Error) {
                    message = `Error getting foreground process: ${e.message}`;
                } else {
                    message = `Error getting foreground process: ${JSON.stringify(e)}`;
                }
                await error(message);
                await mainWindow.show();
                alert(message)
                await mainWindow.hide();
                state.clear();
                return;
            }

            const pid = state.process.pid;
            debug(`Suspending foreground process ${pid}`);
            try {
                await suspendProcess(pid);
            } catch (e) {
                let message;
                if (e instanceof Error) {
                    message = `Error suspending process ${pid}: ${e.message}`;
                } else {
                    message = `Error suspending process ${pid}: ${JSON.stringify(e)}`;
                }
                await error(message);
                await mainWindow.show();
                alert(message)
                await mainWindow.hide();
                state.clear();
                return;
            }

            try {
                state.setScreenshot(await takeScreenshot(state.process.hwnd));
            } catch (e) {
                let message;
                if (e instanceof Error) {
                    message = `Error taking screenshot: ${e.message}`;
                } else {
                    message = `Error taking screenshot: ${JSON.stringify(e)}`;
                }
                await error(message);
                await mainWindow.show();
                alert(message)
                await mainWindow.hide();

                try {
                    await resumeProcess(pid);
                } catch (e) {
                    await error(`Error resuming process ${pid}: ${e}`);
                }

                state.clear();
                return;
            }

            try {
                const googleCloudAPIKey = await settings.getGoogleCloudAPIKeyKey();
                // TODO handle absence of key
                const ocrImageBase64 = await invoke<string>('prepare_screenshot_for_ocr', {screenshotPng: state.screenshotPng, targetHeight: 1080});
                const ocr = await getOcr(ocrImageBase64, googleCloudAPIKey!);
                state.setOcr(ocr);
            } catch (e) {
                await error(`Error getting OCR: ${JSON.stringify(e)}`);
            }

            state.active = true;

            await mainWindow.show();
            // Deal with residual task bar.
            await mainWindow.setDecorations(true);
            await mainWindow.setDecorations(false);
            await mainWindow.setFocus();
        }
    }
}).then(async () => {
    await debug("Global shortcut registered");

    const menu = await Menu.new({
        items: [
            {
                id: 'settings',
                text: 'Settings',
                action: async () => {
                    await settingsWindow?.emitTo(SettingsWindowID, "reload");
                    await settingsWindow?.show()
                }
            },
            {
                id: 'exit',
                text: 'Exit',
                action: async () => await exit(0)
            },
        ],
    });
    const options = {
        id: TrayIconId,
        icon: await defaultWindowIcon(),
        menu,
    };
    await TrayIcon.new(options);
}).catch(async (e) => {
    await error(`Error registering global shortcut: ${e}`);
});
