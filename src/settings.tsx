import React, {useCallback, useEffect, useState} from "react";
import ReactDOM from "react-dom/client";
import {
    FluentProvider,
    Input,
    InputOnChangeData,
    Label,
    makeStyles,
    useId,
    webLightTheme,
    tokens
} from "@fluentui/react-components";
import {error} from "@tauri-apps/plugin-log";
import {getCurrentWindow} from "@tauri-apps/api/window";
import Settings from "./settings.ts";

const settings = new Settings();
try {
    await settings.init();
} catch (e) {
    await error(`Error initializing settings: ${e}`);
    throw e;
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <FluentProvider theme={webLightTheme}>
            <SettingsView />
        </FluentProvider>
    </React.StrictMode>,
);

const useStyles = makeStyles({
    root: {
        display: "flex",
        flexDirection: "column",
        gap: tokens.spacingVerticalXXS,
        maxWidth: "400px",
    },
});

function SettingsView() {
    const googleCloudAPIKeyInput = useId("input");
    const styles = useStyles();
    const [googleCloudAPIKey, setGoogleCloudAPIKey] = useState<string>("");

    useEffect(() => {
        const unlisten = getCurrentWindow().listen("reload", async () => {
            try {
                const v = await settings.getGoogleCloudAPIKeyKey();
                if (!!v) {
                    setGoogleCloudAPIKey(v);
                } else {
                    setGoogleCloudAPIKey("");
                }
            } catch (e) {
                const message = `Error loading config: ${JSON.stringify(e)}`;
                await error(message);
                alert(message);
            }
        });

        return () => {
            unlisten.then(f => f());
        };
    }, []);

    const onGoogleCloudAPIKeyChange = useCallback(async (event: CustomEvent<HTMLInputElement>, data: InputOnChangeData) => {
        try {
            await settings.setGoogleCloudAPIKeyKey(data.value)
            setGoogleCloudAPIKey(data.value);
        } catch (e) {
            const message = `Error storing config: ${JSON.stringify(e)}`;
            await error(message);
            alert(message);
            event.preventDefault();
        }
    }, []);

    return (
        <div className={styles.root}>
            <Label required htmlFor={googleCloudAPIKeyInput}>Google Cloud API key</Label>
            <Input type="password" id={googleCloudAPIKeyInput}
                   value={googleCloudAPIKey}
                   onChange={onGoogleCloudAPIKeyChange} />
        </div>
    );
}
