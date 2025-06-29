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
import {open, readTextFile, writeTextFile} from '@tauri-apps/plugin-fs';
import Settings from "./settings.ts";
import getOcr, {OcrResponse} from "./ocr.ts";
import {FluentProvider, webLightTheme} from "@fluentui/react-components";

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
    active: boolean = false;
    process?: Process;
    screenshotPng?: ArrayBuffer;
    screenshotUrl?: string;
    ocrResult?: OcrResponse;
    loadingError?: string;

    constructor() {
        makeObservable(this, {
            active: observable,
            screenshotUrl: observable,
            ocrResult: observable,
            loadingError: observable,
            setActive: action,
            setScreenshot: action,
            setOcrResult: action,
            setLoadingError: action,
            clear: action,
        });
    }

    setActive() {
        this.active = true;
    }

    setScreenshot(png: ArrayBuffer) {
        this.screenshotPng = new Uint8Array(png);
        const blob = new Blob([new Uint8Array(png)], {type: 'image/png'});
        if (this.screenshotUrl) {
            URL.revokeObjectURL(this.screenshotUrl);
        }
        this.screenshotUrl = URL.createObjectURL(blob);
    }

    setOcrResult(ocrResult: OcrResponse | undefined) {
        this.ocrResult = ocrResult;
    }

    setLoadingError(error: string) {
        this.loadingError = error;
    }

    clear() {
        this.active = false;
        this.process = undefined;
        if (this.screenshotUrl) {
            URL.revokeObjectURL(this.screenshotUrl);
        }
        this.screenshotPng = undefined;
        this.screenshotUrl = undefined;
        this.ocrResult = undefined;
        this.loadingError = undefined;
    }
}

type Process = {
    pid: number;
    hwnd: number;
    scale_factor: number;
};

const state = observable<State>(new State());

const AppWrapper = observer(({state}: {state: State}) => {
    return state.active
        ? <App screenshotUrl={state.screenshotUrl} ocrResult={state.ocrResult} loadingError={state.loadingError} />
        : null
});
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <FluentProvider theme={webLightTheme}>
            <AppWrapper state={state} />
        </FluentProvider>
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

        const configContent = await readTextFile(await invoke("dev_get_path", {file: "dev/screenshots/config.txt"}));
        const lines = configContent.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#'));  // filter out empty lines and comments
        
        if (lines.length === 0) {
            throw new Error("No valid screenshot files found in config");
        }

        const randomIndex = Math.floor(Math.random() * lines.length);
        const selectedFile = lines[randomIndex];

        const screenshotPath = await invoke<string>("dev_get_path", {file: `dev/screenshots/${selectedFile}`});
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

async function runOcr(screenshotPng: ArrayBuffer): Promise<OcrResponse> {
    const ocrImageBase64 = await invoke<string>('prepare_screenshot_for_ocr', {screenshotPng, targetHeight: 1080});

    if (DeveloperFeatures.mockProcessAndScreenshot) {
        await debug("Running OCR in dev mode");
        const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ocrImageBase64));
        const hashHex = Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
        const cacheFile = `dev/ocr_cache/${hashHex}.json`;
        const cachePath = await invoke<string>("dev_get_path", {file: cacheFile});

        try {
            const cachedContent = await readTextFile(cachePath);
            await debug(`OCR cache hit for ${hashHex}`);
            return JSON.parse(cachedContent) as OcrResponse;
        } catch (e) {
            await debug(`OCR cache miss for ${hashHex}, calling API`);
            const result = await callGoogleOcr(ocrImageBase64);
            try {
                await writeTextFile(cachePath, JSON.stringify(result));
                await debug(`OCR result cached to ${hashHex}`);
            } catch (e) {
                await error(`Failed to cache OCR result: ${e}`);
                throw e;
            }

            return result;
        }
    } else {
        return callGoogleOcr(ocrImageBase64);
    }
}

async function callGoogleOcr(ocrImageBase64: string): Promise<OcrResponse> {
    const googleCloudAPIKey = await settings.getGoogleCloudAPIKeyKey();
    // TODO handle absence of key
    return await getOcr(ocrImageBase64, googleCloudAPIKey!);
}

unregister(Shortcut);
register(Shortcut, async (event: ShortcutEvent) => {
    if (event.state === "Pressed") {
        debug('Shortcut pressed');

        if (state.active) {
            await mainWindow.hide();

            if (!state.process) {
                warn(`Session is active, but no process`);
                state.clear();
                return;
            }

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

            state.clear();
        } else {
            state.setActive();

            await mainWindow.show();
            // Deal with residual task bar.
            await mainWindow.setDecorations(true);
            await mainWindow.setDecorations(false);
            await mainWindow.setFocus();

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
                state.setLoadingError(message);
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
                state.setLoadingError(message);
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
                state.setLoadingError(message);
                return;
            }

            try {
                state.setOcrResult(await runOcr(state.screenshotPng!));
            } catch (e) {
                const message = `Error running OCR: ${JSON.stringify(e)}`;
                await error(message);
                state.setLoadingError(message);
                return;
            }
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
