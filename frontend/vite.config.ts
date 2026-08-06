import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit()
	],
	resolve: {
		// Component tests must resolve svelte to the client build (index-client),
		// otherwise mount() fails with "not available on the server". This is the
		// documented setup for @testing-library/svelte with vitest.
		conditions: ['module', 'browser', 'development|production']
	},
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	},
	test: {
		environment: 'jsdom',
		include: ['src/**/*.{test,spec}.{js,ts}']
	}
});
