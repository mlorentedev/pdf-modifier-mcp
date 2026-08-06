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

	describe('highlight precision (AC3)', () => {
		it('crops a partial term to the substring bounds within an item', () => {
			// Item "Hello World" width 110pt: "World" starts at char 6 of 11.
			const items = [item('Hello World', [1, 0, 0, 1, 0, 0], 110, 12)];
			const rects = getHighlightRects('World', items, viewport);

			expect(rects).toHaveLength(1);
			// scale 1.5: full width 165; "World" starts at 6/11 => x = 165 * 6/11 = 90
			expect(rects[0].x).toBeCloseTo(90);
			// "World" is 5/11 of the item => width = 165 * 5/11 = 75
			expect(rects[0].width).toBeCloseTo(75);
		});

		it('matches a term spanning multiple items on the same line', () => {
			// "Hello" (0-40) + "World" (44-88): pdf.js returns them as separate items.
			const items = [
				item('Hello', [1, 0, 0, 1, 0, 0], 40, 12),
				item('World', [1, 0, 0, 1, 44, 0], 44, 12)
			];
			const rects = getHighlightRects('Hello World', items, viewport);

			expect(rects).toHaveLength(2);
			// First item fully covered, second fully covered.
			const fullWidths = rects.every(r => r.width > 0);
			expect(fullWidths).toBe(true);
		});

		it('crops the boundary items of a multi-item match', () => {
			// "Hello Wor" + "ld": the term "World" crosses into the second item.
			const items = [
				item('Hello Wor', [1, 0, 0, 1, 0, 0], 80, 12),
				item('ld', [1, 0, 0, 1, 80, 0], 20, 12)
			];
			const rects = getHighlightRects('World', items, viewport);

			expect(rects).toHaveLength(2);
			// First item: "World" starts at char 6 of 9 => x = 120 * 6/9 = 80; width = 120 * 3/9 = 40
			expect(rects[0].x).toBeCloseTo(80);
			expect(rects[0].width).toBeCloseTo(40);
			// Second item: "ld" fully covered => width = 30
			expect(rects[1].width).toBeCloseTo(30);
		});

		it('does not join items on different baselines', () => {
			const items = [
				item('Hello', [1, 0, 0, 1, 0, 0], 40, 12),
				item('World', [1, 0, 0, 1, 0, 20], 44, 12)
			];
			const rects = getHighlightRects('Hello World', items, viewport);

			expect(rects).toHaveLength(0);
		});
	});
});
