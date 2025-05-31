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

const TrayIconId = 'trayIconId';
const Shortcut = 'Alt+P';
const SettingsWindowID = 'settings';

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

    clear() {
        this.active = false;
        this.process = undefined;
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
                await invoke("resume_process", {pid});
                resumedSuccessfully = true;
            } catch (e) {
                let message = `Error resuming process ${pid}: ${e}`;
                await error(message);
                await mainWindow.show();
                alert(message)
                await mainWindow.hide();
            }

            if (resumedSuccessfully) {
                debug("Restoring foreground window");
                try {
                    await invoke("bring_window_to_foreground", {hwnd: state.process.hwnd});
                } catch (e) {
                    let message = `Error restoring foreground window: ${e}`;
                    await error(message);
                    await getCurrentWindow().show();
                    alert(message)
                    await getCurrentWindow().hide();
                }
            }

            state.active = false;
            state.process = undefined;
        } else {
            debug("Getting foreground process");
            try {
                state.process = await invoke<Process>("get_foreground_process");
            } catch (e) {
                let message = `Error getting foreground process: ${e}`;
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
                await invoke("suspend_process", {pid});
            } catch (e) {
                let message = `Error suspending process ${pid}: ${e}`;
                await error(message);
                await mainWindow.show();
                alert(message)
                await mainWindow.hide();
                state.clear();
                return;
            }

            try {
                state.setScreenshot(await invoke<ArrayBuffer>('take_screenshot', {hwnd: state.process.hwnd}));
            } catch (e) {
                const message = `Error taking screenshot: ${JSON.stringify(e)}`;
                error(message);
                await error(message);
                await mainWindow.show();
                alert(message)
                await mainWindow.hide();

                try {
                    await invoke("resume_process", {pid});
                } catch (e) {
                    await error(`Error resuming process ${pid}: ${e}`);
                }

                state.clear();
                return;
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
