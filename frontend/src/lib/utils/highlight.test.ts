import { describe, expect, it } from 'vitest';
import { getHighlightRects, type HighlightTextItem, type HighlightViewport } from './highlight';

// A default viewport: scale 1.5, no rotation, no offset.
// transform layout (pdf.js PageViewport): [a, b, c, d, e, f]
const viewport: HighlightViewport = {
	scale: 1.5,
	transform: [1.5, 0, 0, 1.5, 0, 0]
};

function item(str: string, transform: number[], width: number, height: number): HighlightTextItem {
	return { str, transform, width, height };
}

describe('getHighlightRects', () => {
	it('returns an empty array when the term is empty or whitespace', () => {
		const items = [item('Hello', [1, 0, 0, 1, 0, 0], 50, 12)];
		expect(getHighlightRects('', items, viewport)).toEqual([]);
		expect(getHighlightRects('   ', items, viewport)).toEqual([]);
	});

	it('returns an empty array when no items match', () => {
		const items = [item('Hello world', [1, 0, 0, 1, 0, 0], 100, 12)];
		expect(getHighlightRects('xyz', items, viewport)).toEqual([]);
	});

	it('returns an empty array when the items list is empty', () => {
		expect(getHighlightRects('Hello', [], viewport)).toEqual([]);
	});

	it('matches case-insensitively', () => {
		const items = [item('Hello World', [1, 0, 0, 1, 0, 0], 100, 12)];
		const rects = getHighlightRects('hello', items, viewport);
		expect(rects).toHaveLength(1);
	});

	it('computes rect in canvas space: position from transform, size from scale', () => {
		// Item at PDF origin (0,0), width 100pt, height 12pt.
		const items = [item('Hello', [1, 0, 0, 1, 0, 0], 100, 12)];
		const rects = getHighlightRects('Hello', items, viewport);

		expect(rects).toHaveLength(1);
		const r = rects[0];
		// Scale 1.5 => width 150px, height 18px
		expect(r.width).toBeCloseTo(150);
		expect(r.height).toBeCloseTo(18);
		// Origin x=0; baseline y=0 minus height => top edge at -18
		expect(r.x).toBeCloseTo(0);
		expect(r.y).toBeCloseTo(-18);
	});

	it('accounts for viewport translation (page offset)', () => {
		// Page offset by (10, 20) in canvas coords.
		const vp: HighlightViewport = {
			scale: 1,
			transform: [1, 0, 0, 1, 10, 20]
		};
		const items = [item('Hello', [1, 0, 0, 1, 0, 0], 40, 12)];
		const rects = getHighlightRects('Hello', items, vp);

		expect(rects).toHaveLength(1);
		expect(rects[0].x).toBeCloseTo(10);
		expect(rects[0].y).toBeCloseTo(20 - 12);
	});

	it('handles item-level transform (positioned text)', () => {
		// Item placed at PDF (100, 200).
		const items = [item('Hello', [1, 0, 0, 1, 100, 200], 40, 12)];
		const rects = getHighlightRects('Hello', items, viewport);

		expect(rects).toHaveLength(1);
		const r = rects[0];
		// x = 100 * 1.5 = 150; baseline y = 200 * 1.5 = 300; top = 300 - 18
		expect(r.x).toBeCloseTo(150);
		expect(r.y).toBeCloseTo(300 - 18);
	});

	it('matches every item that contains the term', () => {
		const items = [
			item('Hello world', [1, 0, 0, 1, 0, 0], 100, 12),
			item('Say hello again', [1, 0, 0, 1, 0, 20], 120, 12),
			item('Nothing here', [1, 0, 0, 1, 0, 40], 90, 12)
		];
		const rects = getHighlightRects('hello', items, viewport);
		expect(rects).toHaveLength(2);
	});

	it('clamps negative widths/heights to zero', () => {
		const items = [item('Hello', [1, 0, 0, 1, 0, 0], -10, -5)];
		const rects = getHighlightRects('Hello', items, viewport);
		expect(rects).toHaveLength(1);
		expect(rects[0].width).toBe(0);
		expect(rects[0].height).toBe(0);
	});
});
