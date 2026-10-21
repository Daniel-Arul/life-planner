/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

// Caches the app itself (code, styles, fonts, icons) so it opens instantly and
// can show a friendly "can't reach the Pi" message offline. Your data (/api)
// is never cached: it always comes live from the Pi.
import { build, files, version } from '$service-worker';

const sw = self as unknown as ServiceWorkerGlobalScope;
const CACHE = `planner-${version}`;
// "/" is the SPA shell: FastAPI serves the same index.html for every page.
const SHELL = '/';
const PRECACHE = [SHELL, ...build, ...files];

sw.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE)
			.then((cache) => cache.addAll(PRECACHE))
			.then(() => sw.skipWaiting())
	);
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
			.then(() => sw.clients.claim())
	);
});

sw.addEventListener('fetch', (event) => {
	const request = event.request;
	const url = new URL(request.url);
	if (request.method !== 'GET' || url.origin !== sw.location.origin) return;
	if (url.pathname.startsWith('/api/')) return; // always live

	if (request.mode === 'navigate') {
		// Pages: try the network (picks up new versions), fall back to the cached shell.
		event.respondWith(
			fetch(request).catch(async () => (await caches.match(SHELL)) ?? Response.error())
		);
		return;
	}

	// Built assets and static files: cache first, they're versioned.
	event.respondWith(
		caches.match(request).then((cached) => cached ?? fetch(request))
	);
});
