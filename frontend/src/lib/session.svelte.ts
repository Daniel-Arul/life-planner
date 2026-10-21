import { api, ApiError } from './api';

export type User = { id: number; username: string };

class Session {
	user = $state<User | null>(null);
	loaded = $state(false);

	async load() {
		try {
			this.user = await api.get<User>('/auth/me');
		} catch (err) {
			if (!(err instanceof ApiError && err.status === 401)) throw err;
			this.user = null;
		} finally {
			this.loaded = true;
		}
	}

	async login(username: string, password: string) {
		this.user = await api.post<User>('/auth/login', { username, password });
	}

	async logout() {
		await api.post('/auth/logout');
		this.user = null;
	}
}

export const session = new Session();
