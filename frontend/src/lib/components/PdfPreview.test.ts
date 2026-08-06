import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/svelte';
import PdfPreview from './PdfPreview.svelte';

// --- Mock pdf.js so no real worker/PDF is needed in jsdom ---
// Track render tasks so the test can assert cancel-before-render semantics.
const { mockDoc, renderCalls, cancelled } = vi.hoisted(() => {
	const renderCalls: Array<{ page: number; cancelled: boolean }> = [];
	const cancelled: number[] = [];

	function makePage(n: number) {
		return {
			getViewport: vi.fn(() => ({
				scale: 1.5,
				transform: [1.5, 0, 0, 1.5, 0, 0],
				width: 600,
				height: 800
			})),
			render: vi.fn(() => {
				const record = { page: n, cancelled: false };
				renderCalls.push(record);
				let rejectFn: (e: Error) => void = () => {};
				const promise = new Promise<void>((_, reject) => {
					rejectFn = reject;
				});
				return {
					promise,
					cancel: vi.fn(() => {
						record.cancelled = true;
						cancelled.push(n);
						rejectFn(new Error('RenderingCancelledException'));
						rejectFn = () => {};
					})
				};
			}),
			getTextContent: vi.fn(() => Promise.resolve({ items: [] }))
		};
	}

	return {
		mockDoc: {
			numPages: 2,
			getPage: vi.fn(async (n: number) => makePage(n))
		},
		renderCalls,
		cancelled
	};
});

vi.mock('pdfjs-dist', () => ({
	GlobalWorkerOptions: { workerSrc: '' },
	getDocument: vi.fn(() => ({ promise: Promise.resolve(mockDoc) }))
}));

// jsdom has no canvas 2D context; provide a minimal fake so renderPage proceeds.
beforeEach(() => {
	renderCalls.length = 0;
	cancelled.length = 0;
	HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
		fillRect: vi.fn(),
		fillStyle: ''
	})) as unknown as typeof HTMLCanvasElement.prototype.getContext;
	globalThis.fetch = vi.fn(async () => ({
		arrayBuffer: async () => new ArrayBuffer(8)
	})) as unknown as typeof fetch;
});

describe('PdfPreview render coordination (regression: same-canvas render error)', () => {
	it('reuses the in-flight render when the highlight effect and locate effect fire together', async () => {
		const { component, rerender } = render(PdfPreview, { sessionId: 's1' });

		// Wait for the initial load render.
		await waitFor(() => {
			expect(renderCalls.length).toBeGreaterThanOrEqual(1);
		});
		const initialCalls = renderCalls.length;

		// Simulate a sidebar click: highlightText AND focusTarget change together,
		// same page. Before the fix this started a SECOND render (locate effect)
		// on the same canvas while the highlight render was still in flight ->
		// "Cannot use the same canvas during multiple render()".
		await rerender({ highlightText: 'Hello World', focusTarget: { page: 1, bbox: [0, 0, 50, 12] } });
		await new Promise(r => setTimeout(r, 30));

		// Exactly one new render: the highlight effect's re-render. The locate
		// effect must reuse it (renderPromise) instead of starting a second one.
		expect(renderCalls.length).toBe(initialCalls + 1);
	});

	it('cancels the previous render before starting one on a different page', async () => {
		const { rerender } = render(PdfPreview, { sessionId: 's2' });

		await waitFor(() => {
			expect(renderCalls.length).toBeGreaterThanOrEqual(1);
		});

		// Navigate to page 2 via focusTarget (page change).
		await rerender({ focusTarget: { page: 2, bbox: [0, 0, 50, 12] } });
		await new Promise(r => setTimeout(r, 30));

		// A render for page 2 was started...
		expect(renderCalls.some(c => c.page === 2)).toBe(true);
		// ...and any page-1 render that was still in flight was cancelled first
		// (otherwise pdf.js throws the same-canvas error).
		const page1Calls = renderCalls.filter(c => c.page === 1);
		expect(page1Calls.length).toBeGreaterThan(0);
		expect(page1Calls.some(c => c.cancelled)).toBe(true);
	});
});
