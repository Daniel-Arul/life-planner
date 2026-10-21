import { api, ApiError, SESSION_EXPIRED, UNREACHABLE } from './api';

export type User = { id: number; username: string };

class Session {
	user = $state<User | null>(null);
	loaded = $state(false);

	async load() {
		try {
			this.user = await api.get<User>('/auth/me');
		} catch (err) {
			// Not logged in, or the Pi can't be reached (the layout shows which).
			if (!(err instanceof ApiError && (err.status === 401 || err.status === UNREACHABLE))) throw err;
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

if (typeof window !== 'undefined') {
	window.addEventListener(SESSION_EXPIRED, () => {
		session.user = null; // the root layout redirects to /login
	});
}
