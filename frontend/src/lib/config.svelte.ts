import { api } from './api';

/** Server-provided display settings (currency comes from PLANNER_CURRENCY). */
class AppConfig {
	currency = $state('CAD');
	#loaded = false;

	async load() {
		if (this.#loaded) return;
		try {
			const config = await api.get<{ currency: string }>('/config');
			this.currency = config.currency;
			this.#loaded = true;
		} catch {
			// Keep the default; money still renders, just possibly in the wrong currency.
		}
	}
}

export const appConfig = new AppConfig();
