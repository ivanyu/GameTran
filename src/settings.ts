import {Store} from "@tauri-apps/plugin-store";

const GoogleCloudAPIKeyKey = "google_cloud_api_key";

class Settings {
    private store: Store

    // TODO more secure storage for secrets.

    public async init() {
        this.store = await Store.load('settings.json');
    }

    public async setGoogleCloudAPIKeyKey(value: string | undefined) {
        await this.store.set(GoogleCloudAPIKeyKey, value);
    }

    public async getGoogleCloudAPIKeyKey(): Promise<string | undefined> {
        await this.store.reload();
        return await this.store.get<string>(GoogleCloudAPIKeyKey);
    }
}

export default Settings;
