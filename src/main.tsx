import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import {observable} from "mobx";
import {register, ShortcutEvent} from "@tauri-apps/plugin-global-shortcut";
import {debug, error} from "@tauri-apps/plugin-log";
import {getCurrentWindow} from "@tauri-apps/api/window";
import { observer } from "mobx-react-lite";

const Shortcut = 'Alt+P';

const session = observable({
    active: false
});

const AppWrapper = observer(() => session.active
    ? <App />
    : null);
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <AppWrapper />
    </React.StrictMode>,
);

register(Shortcut, async (event: ShortcutEvent) => {
    if (event.state === "Pressed") {
        debug('Shortcut pressed');

        if (session.active) {
            session.active = false;
            await getCurrentWindow().hide();
        } else {
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
