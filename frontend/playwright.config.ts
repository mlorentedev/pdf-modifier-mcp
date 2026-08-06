import { defineConfig } from '@playwright/test';

/**
 * E2E config — validates the web UI against the real Docker stack.
 *
 * The stack is brought up by `make up` (API :8000, web :8080). Playwright
 * reuses a running stack (reuseExistingServer) and starts it otherwise.
 *
 *   npx playwright test            # run all e2e specs
 *   npx playwright test -g "group" # filter by name
 *   npx playwright show-report     # view last run
 */
export default defineConfig({
	testDir: './e2e',
	fullyParallel: true,
	timeout: 60_000,
	retries: process.env.CI ? 2 : 0,
	reporter: [['list'], ['html', { open: 'never' }]],
	use: {
		baseURL: 'http://localhost:8080',
		trace: 'retain-on-failure',
		screenshot: 'only-on-failure'
	},
	webServer: {
		command: 'cd .. && make up',
		url: 'http://localhost:8080/health',
		reuseExistingServer: true,
		timeout: 120_000
	},
	projects: [{ name: 'chromium', use: { browserName: 'chromium' } }]
});
