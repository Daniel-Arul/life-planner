import { api } from './api';

/** Server-provided display settings (PLANNER_CURRENCY and PLANNER_UNITS). */
class AppConfig {
	currency = $state('CAD');
	units = $state<'metric' | 'imperial'>('metric');
	#loaded = false;

	async load() {
		if (this.#loaded) return;
		try {
			const config = await api.get<{ currency: string; units: 'metric' | 'imperial' }>('/config');
			this.currency = config.currency;
			this.units = config.units;
			this.#loaded = true;
		} catch {
			// Keep the default; money still renders, just possibly in the wrong currency.
		}
	}
}

export const appConfig = new AppConfig();
