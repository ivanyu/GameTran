import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import {observable} from "mobx";
import {register, ShortcutEvent, unregister} from "@tauri-apps/plugin-global-shortcut";
import {debug, error, warn} from "@tauri-apps/plugin-log";
import {getCurrentWindow} from "@tauri-apps/api/window";
import { observer } from "mobx-react-lite";
import {invoke} from "@tauri-apps/api/core";

const Shortcut = 'Alt+P';

type State = {
    active: boolean;
    process?: Process;
}

type Process = {
    pid: number;
    hwnd: number;
    scale_factor: number;
};

const session = observable<State>({
    active: false,
    process: undefined,
});

const AppWrapper = observer(() => session.active
    ? <App />
    : null);
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <AppWrapper />
    </React.StrictMode>,
);

unregister(Shortcut);
register(Shortcut, async (event: ShortcutEvent) => {
    if (event.state === "Pressed") {
        debug('Shortcut pressed');

        if (session.active) {
            if (!session.process) {
                warn(`Session is active, but no process`);
                return;
            }

            await getCurrentWindow().hide();

            // Don't "optimize" hiding and showing here: the chance of an error in resuming is small and that's OK to pay for it with a bit of flickering
            // to allow the window hide in the normal circumstances faster.
            const pid = session.process.pid;
            debug(`Resuming foreground process ${pid}`);
            try {
                await invoke("resume_process", {pid});
            } catch (e) {
                let message = `Error resuming process ${pid}: ${e}`;
                await error(message);
                await getCurrentWindow().show();
                alert(message)
                await getCurrentWindow().hide();
            }

            session.active = false;
            session.process = undefined;
        } else {
            debug("Getting foreground process");
            try {
                session.process = await invoke<Process>("get_foreground_process");
            } catch (e) {
                let message = `Error getting foreground process: ${e}`;
                await error(message);
                await getCurrentWindow().show();
                alert(message)
                await getCurrentWindow().hide();
                return;
            }

            const pid = session.process.pid;
            debug(`Suspending foreground process ${pid}`);
            try {
                await invoke("suspend_process", {pid});
            } catch (e) {
                let message = `Error suspending process ${pid}: ${e}`;
                await error(message);
                await getCurrentWindow().show();
                alert(message)
                await getCurrentWindow().hide();
                return;
            }

            session.active = true;

            await getCurrentWindow().show();
            // Deal with residual task bar.
            await getCurrentWindow().setDecorations(true);
            await getCurrentWindow().setDecorations(false);
            await getCurrentWindow().setFocus();
        }
    }
}).then(async () => {
    await debug("Global shortcut registered");
}).catch(async (e) => {
    await error(`Error registering global shortcut: ${e}`);
});
