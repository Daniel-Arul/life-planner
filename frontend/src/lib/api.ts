import { connection } from './connection.svelte';

/** Fired on window when an API call comes back 401 outside /auth. */
export const SESSION_EXPIRED = 'planner:session-expired';

/** Status 0 means the request never reached the planner. */
export const UNREACHABLE = 0;

export class ApiError extends Error {
	status: number;

	constructor(status: number, message: string) {
		super(message);
		this.status = status;
	}
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
	let res: Response;
	try {
		res = await fetch(`/api${path}`, {
			method,
			credentials: 'same-origin',
			headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
			body: body === undefined ? undefined : JSON.stringify(body)
		});
	} catch {
		connection.reachable = false;
		throw new ApiError(UNREACHABLE, "Can't reach your planner. Is Tailscale connected?");
	}
	// 502-504 come from `tailscale serve` when the app container isn't running.
	if (res.status >= 502 && res.status <= 504) {
		connection.reachable = false;
		throw new ApiError(UNREACHABLE, "Your planner isn't responding. Is it running on the Pi?");
	}
	connection.reachable = true;

	// The session expired mid-use: let the session store send us to the login page.
	if (res.status === 401 && !path.startsWith('/auth/')) {
		window.dispatchEvent(new Event(SESSION_EXPIRED));
	}

	if (!res.ok) {
		let message = res.statusText || `Request failed (${res.status})`;
		try {
			const data = await res.json();
			if (typeof data.detail === 'string') message = data.detail;
		} catch {
			// Non-JSON error body; keep the status text.
		}
		throw new ApiError(res.status, message);
	}

	if (res.status === 204) return undefined as T;
	return (await res.json()) as T;
}

export const api = {
	get: <T>(path: string) => request<T>('GET', path),
	post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
	put: <T>(path: string, body: unknown) => request<T>('PUT', path, body),
	patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
	delete: <T = void>(path: string) => request<T>('DELETE', path)
};
