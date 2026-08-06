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

	it('does not merge spans with different fonts', () => {
		const elements = [
			el('Hello', 0, 0, 40, 12, 'Helvetica', 12),
			el('World', 44, 0, 88, 12, 'Times-Roman', 12)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(2);
	});

	it('does not merge spans with different font sizes', () => {
		const elements = [
			el('Hello', 0, 0, 40, 12, 'Helvetica', 12),
			el('World', 44, 0, 88, 16, 'Helvetica', 16)
		];
		const groups = groupElements(elements);

		expect(groups).toHaveLength(2);
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

		it('drops a leading space span from the group text and bbox', () => {
			// Style change inside a line: 'Different'(helv) then ' '(Times) 'Font'(Times).
			const elements = [
				el('Different', 0, 0, 53, 12, 'Helvetica', 12),
				el(' ', 53, 0, 58, 12, 'Times-Roman', 12),
				el('Font', 58, 0, 84, 12, 'Times-Roman', 12)
			];
			const groups = groupElements(elements);

			// 'Different' can't merge (different font); ' ' + 'Font' merge.
			expect(groups).toHaveLength(2);
			expect(groups[0].text).toBe('Different');
			expect(groups[1].text).toBe('Font'); // leading space trimmed
			expect(groups[1].bbox).toEqual([58, 0, 84, 12]); // no space in bbox
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
