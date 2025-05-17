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
import {Store} from '@tauri-apps/plugin-store'
import {getCurrentWindow} from "@tauri-apps/api/window";

const GoogleCloudAPIKeyKey = "google_cloud_api_key";

const store = await Store.load('settings.json')

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <FluentProvider theme={webLightTheme}>
            <Settings />
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

function Settings() {
    const googleCloudAPIKeyInput = useId("input");
    const styles = useStyles();
    const [googleCloudAPIKey, setGoogleCloudAPIKey] = useState<string>("");

    useEffect(() => {
        const unlisten = getCurrentWindow().listen("reload", async () => {
            try {
                await store.reload();
                // TODO more secure storage for secrets.
                const v = await store.get<string>(GoogleCloudAPIKeyKey);
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
            await store.set(GoogleCloudAPIKeyKey, data.value);
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
