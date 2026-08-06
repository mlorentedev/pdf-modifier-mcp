import { describe, expect, it } from 'vitest';
import { groupElements, type ElementGroup, type TextElement } from './grouping';

function el(
	text: string,
	x0: number,
	y0: number,
	x1: number,
	y1: number,
	font = 'Helvetica',
	size = 12,
	baseline?: number
): TextElement {
	return {
		text,
		bbox: [x0, y0, x1, y1],
		origin: [x0, baseline ?? y1],
		font,
		size,
		color: 0
	};
}

describe('groupElements', () => {
	it('returns an empty array for an empty element list', () => {
		expect(groupElements([])).toEqual([]);
	});

	it('merges consecutive spans on the same line into one group', () => {
		// "Hello" (0-40) then "World" (44-88): gap 4pt on a 12pt baseline.
		const elements = [
			el('Hello', 0, 0, 40, 12, 'Helvetica', 12),
			el('World', 44, 0, 88, 12, 'Helvetica', 12)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(1);
		expect(groups[0].text).toBe('Hello World');
		// Merged bbox spans both words (x0 of first, x1 of last).
		expect(groups[0].bbox).toEqual([0, 0, 88, 12]);
		// Origin taken from the first span.
		expect(groups[0].origin).toEqual([0, 12]);
	});

	it('does not merge spans separated by a gap larger than the threshold', () => {
		// Two columns: "Hello" at x=0, "World" at x=200 (gap 160pt >> 1.2*12).
		const elements = [
			el('Hello', 0, 0, 40, 12),
			el('World', 200, 0, 244, 12)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(2);
		expect(groups[0].text).toBe('Hello');
		expect(groups[1].text).toBe('World');
	});

	it('does not merge spans on different baselines (different lines)', () => {
		const elements = [
			el('Hello', 0, 0, 40, 12),
			el('World', 44, 20, 88, 32)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(2);
	});

	it('does not merge spans with different fonts at medium gap', () => {
		// Gap 8pt is within weak-merge range (1.2*12=14.4) but above the strong
		// threshold (0.5*12=6); different fonts fail the weak rule.
		const elements = [
			el('Hello', 0, 0, 40, 12, 'Helvetica', 12),
			el('World', 48, 0, 92, 12, 'Times-Roman', 12)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(2);
	});

	it('does not merge spans with different font sizes at medium gap', () => {
		// Strong threshold uses max size (0.5*16=8); gap 10 is above it and the
		// weak rule requires equal sizes.
		const elements = [
			el('Hello', 0, 0, 40, 12, 'Helvetica', 12),
			el('World', 50, 0, 94, 16, 'Helvetica', 16)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(2);
	});

	it('merges spans with different fonts when tightly packed (strong rule)', () => {
		// Mid-word style run: same visual word, different font name (common with
		// subset/Type3 fonts) and no gap -> strong rule merges.
		const elements = [
			el('B', 0, 0, 8, 12, 'Type3 (16 0 R)', 12),
			el('ooking', 8, 0, 40, 12, 'Type3 (17 0 R)', 12)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(1);
		expect(groups[0].text).toBe('Booking'); // no space: contiguous fragments
	});

	it('merges Type3 fragments with negative gaps and space spans into words', () => {
		// Real data from a FareHarbor ticket: glyph runs split across Type3
		// resource names, explicit space spans between words.
		const elements = [
			el('T', 0, 0, 7.2, 12, 'Type3 (16 0 R)', 12),
			el('se', 6.44, 0, 19.02, 12, 'Type3 (17 0 R)', 12), // gap -0.76
			el(' ', 19.02, 0, 21.86, 12, 'Type3 (18 0 R)', 12),
			el('B', 21.86, 0, 29.82, 12, 'Type3 (16 0 R)', 12),
			el('igh', 29.82, 0, 47.24, 12, 'Type3 (17 0 R)', 12),
			el('a', 47.24, 0, 53.76, 12, 'Type3 (16 0 R)', 12),
			el('nilini', 53.76, 0, 81.44, 12, 'Type3 (17 0 R)', 12)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(1);
		expect(groups[0].text).toBe('Tse Bighanilini');
	});

	it('merges three consecutive spans into one group', () => {
		const elements = [
			el('Hello', 0, 0, 40, 12),
			el('brave', 44, 0, 80, 12),
			el('world', 84, 0, 128, 12)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(1);
		expect(groups[0].text).toBe('Hello brave world');
		expect(groups[0].bbox).toEqual([0, 0, 128, 12]);
	});

	it('splits lines and merges within each line independently', () => {
		const elements = [
			el('Hello', 0, 0, 40, 12),
			el('World', 44, 0, 88, 12),
			el('Second', 0, 20, 52, 32),
			el('Line', 56, 20, 88, 32)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(2);
		expect(groups[0].text).toBe('Hello World');
		expect(groups[1].text).toBe('Second Line');
	});

	it('tolerates float jitter in baseline values on the same line', () => {
		const elements = [
			el('Hello', 0, 0, 40, 12, 'Helvetica', 12, 12.0001),
			el('World', 44, 0, 88, 12, 'Helvetica', 12, 11.9998)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(1);
		expect(groups[0].text).toBe('Hello World');
	});

	it('keeps the per-span list in the group for downstream highlight/locate', () => {
		const elements = [
			el('Hello', 0, 0, 40, 12),
			el('World', 44, 0, 88, 12)
		];
		const groups = groupElements(elements) as ElementGroup[];

		expect(groups[0].elements).toHaveLength(2);
		expect(groups[0].elements[0].text).toBe('Hello');
		expect(groups[0].elements[1].text).toBe('World');
	});

	describe('PyMuPDF real-world spans (explicit space spans)', () => {
		it('merges word + space span + word into a single spaced group', () => {
			// PyMuPDF emits 'Hello' (0-32), ' ' (32-37), 'World' (37-73).
			const elements = [
				el('Hello', 0, 0, 32, 12),
				el(' ', 32, 0, 37, 12),
				el('World', 37, 0, 73, 12)
			];
			const groups = groupElements(elements);

			expect(groups).toHaveLength(1);
			expect(groups[0].text).toBe('Hello World'); // single space, no doubles
			expect(groups[0].bbox).toEqual([0, 0, 73, 12]);
		});

		it('merges a tight style change with a space span into one group', () => {
			// Style change inside a line: 'Different'(helv) + ' '(Times) + 'Font'(Times)
			// with zero gaps. Strong rule merges them (tight = same visual run).
			const elements = [
				el('Different', 0, 0, 53, 12, 'Helvetica', 12),
				el(' ', 53, 0, 58, 12, 'Times-Roman', 12),
				el('Font', 58, 0, 84, 12, 'Times-Roman', 12)
			];
			const groups = groupElements(elements);

			expect(groups).toHaveLength(1);
			expect(groups[0].text).toBe('Different Font');
			expect(groups[0].bbox).toEqual([0, 0, 84, 12]);
		});

		it('drops a leading space span from the group text and bbox', () => {
			// A group that starts with an explicit space span (stray leading space).
			const elements = [
				el(' ', 0, 0, 5, 12, 'Helvetica', 12),
				el('Font', 5, 0, 31, 12, 'Helvetica', 12)
			];
			const groups = groupElements(elements);

			expect(groups).toHaveLength(1);
			expect(groups[0].text).toBe('Font'); // leading space trimmed
			expect(groups[0].bbox).toEqual([5, 0, 31, 12]); // no space in bbox
		});

		it('keeps real inner spaces when a group contains multiple words', () => {
			const elements = [
				el('Hello', 0, 0, 32, 12),
				el(' ', 32, 0, 37, 12),
				el('World', 37, 0, 73, 12),
				el(' ', 73, 0, 78, 12),
				el('Again', 78, 0, 110, 12)
			];
			const groups = groupElements(elements);

			expect(groups).toHaveLength(1);
			expect(groups[0].text).toBe('Hello World Again');
		});
	});
});
