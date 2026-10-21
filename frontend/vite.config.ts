import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		// In dev, forward API calls to uvicorn so cookies stay same-origin.
		proxy: { '/api': 'http://127.0.0.1:8000' }
	}
});
