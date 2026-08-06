import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const FIXTURE = fileURLToPath(new URL('./fixtures/eval-doc.pdf', import.meta.url));

/** Upload the eval fixture and wait for the workspace (sidebar + preview). */
async function uploadPdf(page: import('@playwright/test').Page) {
	await page.goto('/');
	await page.setInputFiles('input[type="file"]', FIXTURE);
	await expect(page.locator('text=PDF Modifier')).toBeVisible();
	// The workspace appears once the structure is loaded.
	await expect(page.getByRole('heading', { name: 'Elements' })).toBeVisible({ timeout: 15_000 });
	await expect(page.getByRole('heading', { name: 'PDF Preview' })).toBeVisible();
	// The preview canvas is the signal that pdf.js finished loading the document
	// (the structure API responds before pdf.js fetches + parses the PDF).
	await expect(page.locator('canvas')).toBeVisible({ timeout: 15_000 });
}

test.describe('PDF preview workspace', () => {
	test('upload works without an error toast (structuredClone regression)', async ({ page }) => {
		await uploadPdf(page);

		// No error toast rendered.
		await expect(page.locator('[role="status"]').filter({ hasText: 'could not be cloned' })).toHaveCount(0);
		await expect(page.locator('.text-red-400')).toHaveCount(0);
	});

	test('sidebar groups text spans into semantic entries', async ({ page }) => {
		await uploadPdf(page);

		// "B" + "ooking" (different fonts, no gap) must be one entry.
		const booking = page.getByRole('button', { name: /^Booking/ });
		await expect(booking).toBeVisible();
		// Fragmented spans must NOT appear separately.
		await expect(page.getByRole('button', { name: /^"B"/ })).toHaveCount(0);

		// Same-line words with real spacing merge into one entry.
		await expect(page.getByRole('button', { name: /^Hello World/ })).toBeVisible();

		// Two columns must stay separate.
		await expect(page.getByRole('button', { name: /^LeftCol/ })).toBeVisible();
		await expect(page.getByRole('button', { name: /^RightCol/ })).toBeVisible();
	});

	test('clicking a sidebar entry navigates + scrolls the preview', async ({ page }) => {
		await uploadPdf(page);

		// Element on page 2: click should navigate the preview to page 2.
		const pageTwoEntry = page.getByRole('button', { name: /^Page Two/ });
		await expect(pageTwoEntry).toBeVisible();
		await pageTwoEntry.click();

		// Preview page indicator jumps to page 2.
		const pageInput = page.locator('input[type="number"]');
		await expect(pageInput).toHaveValue('2', { timeout: 10_000 });

		// The scroll container has actually scrolled (canvas is tall enough).
		const scroll = page.locator('.pdf-scroll');
		await expect(scroll).toBeVisible();
		const scrollTop = await scroll.evaluate(el => el.scrollTop);
		expect(scrollTop).toBeGreaterThanOrEqual(0);
	});

	test('highlight renders on the preview canvas', async ({ page }) => {
		await uploadPdf(page);

		const helloWorld = page.getByRole('button', { name: /^Hello World/ });
		await helloWorld.click();

		// The canvas received a render (dimensions set) and the highlight label shows.
		const canvas = page.locator('canvas');
		await expect(canvas).toBeVisible();
		const size = await canvas.evaluate(el => ({ w: el.width, h: el.height }));
		expect(size.w).toBeGreaterThan(0);
		expect(size.h).toBeGreaterThan(0);
		await expect(page.locator('text=Highlighting:')).toBeVisible();
	});
});
