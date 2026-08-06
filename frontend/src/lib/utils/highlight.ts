/* Pure helpers for computing PDF text highlight rectangles.
 * Kept framework-free so they can be unit-tested without a browser/
 * canvas. A highlight rect is expressed in rendered canvas coordinates.
 */

export interface HighlightRect {
	x: number;
	y: number;
	width: number;
	height: number;
}

export interface HighlightTextItem {
	str: string;
	transform: number[];
	width: number;
	height: number;
}

export interface HighlightViewport {
	scale: number;
	transform: number[];
}

/** Baseline tolerance (PDF points) for items on the same visual line. */
const BASELINE_EPSILON = 0.5;

/** Basic 6-element 2D affine transform composition (same layout as pdf.js). */
function transform(t1: number[], t2: number[]): number[] {
	return [
		t1[0] * t2[0] + t1[2] * t2[1],
		t1[1] * t2[0] + t1[3] * t2[1],
		t1[0] * t2[2] + t1[2] * t2[3],
		t1[1] * t2[2] + t1[3] * t2[3],
		t1[0] * t2[4] + t1[2] * t2[5] + t1[4],
		t1[1] * t2[4] + t1[3] * t2[5] + t1[5]
	];
}

function clamp(value: number, min: number, max: number): number {
	return Math.min(Math.max(value, min), max);
}

function itemRect(item: HighlightTextItem, viewport: HighlightViewport): HighlightRect {
	const tx = transform(viewport.transform, item.transform);
	const width = item.width * viewport.scale;
	const height = item.height * viewport.scale;
	return {
		x: tx[4],
		y: tx[5] - height,
		width: Math.max(0, width),
		height: Math.max(0, height)
	};
}

/** Estimate the canvas-space rect of the substring [start, end) of `item`. */
function subRect(
	item: HighlightTextItem,
	start: number,
	end: number,
	viewport: HighlightViewport
): HighlightRect {
	const full = itemRect(item, viewport);
	const len = item.str.length;
	if (len <= 0) return full;

	const subStart = clamp(start, 0, len);
	const subEnd = clamp(end, 0, len);
	const startFrac = subStart / len;
	const widthFrac = Math.max(0, (subEnd - subStart) / len);

	return {
		x: full.x + full.width * startFrac,
		y: full.y,
		width: full.width * widthFrac,
		height: full.height
	};
}

interface LineItem {
	item: HighlightTextItem;
	/** Start char offset of this item's text within the joined line string. */
	lineStart: number;
}

interface TextLine {
	baseline: number;
	items: LineItem[];
	text: string;
}

/**
 * Group text items into visual lines by baseline (transform[5], PDF space),
 * preserving reading order (left to right within a line). Items whose
 * baseline differs by more than BASELINE_EPSILON start a new line.
 */
function groupLines(items: HighlightTextItem[]): TextLine[] {
	const lines: TextLine[] = [];
	for (const item of items) {
		if (!item.str) continue;
		const baseline = item.transform[5];
		let line = lines.find(l => Math.abs(l.baseline - baseline) <= BASELINE_EPSILON);
		if (!line) {
			line = { baseline, items: [], text: '' };
			lines.push(line);
		}
		line.items.push({ item, lineStart: line.text.length });
		line.text += item.str;
	}
	// Reading order: sort items left-to-right by x offset (transform[4]).
	for (const line of lines) {
		line.items.sort((a, b) => a.item.transform[4] - b.item.transform[4]);
		// Recompute text + lineStart offsets after sorting. A space is inserted
		// between items only when there is a horizontal gap (i.e. a real word
		// boundary); visually contiguous items (one word split by a style
		// change) join without a separator.
		let offset = 0;
		let prevX1 = -Infinity;
		for (const li of line.items) {
			const x0 = li.item.transform[4];
			if (offset > 0 && x0 > prevX1 + 0.5) {
				offset += 1; // one space between words
			}
			li.lineStart = offset;
			offset += li.item.str.length;
			prevX1 = x0 + li.item.width;
		}
		const parts: string[] = [];
		let pos = 0;
		for (const li of line.items) {
			if (pos > 0 && li.lineStart > pos) parts.push(' ');
			parts.push(li.item.str);
			pos = li.lineStart + li.item.str.length;
		}
		line.text = parts.join('');
	}
	return lines;
}

/**
 * Compute canvas-space highlight rectangles for every occurrence of the
 * search term (case-insensitive). Matches may span several text items on the
 * same visual line: the leading/trailing item of a multi-item match is
 * cropped proportionally to the substring bounds. Returns an empty array
 * when the term or items are empty.
 */
export function getHighlightRects(
	term: string,
	items: HighlightTextItem[],
	viewport: HighlightViewport
): HighlightRect[] {
	const trimmed = term.trim();
	if (!trimmed) return [];
	if (items.length === 0) return [];

	const termLower = trimmed.toLowerCase();
	const rects: HighlightRect[] = [];

	for (const line of groupLines(items)) {
		const lineLower = line.text.toLowerCase();
		let fromIndex = 0;
		while (true) {
			const matchStart = lineLower.indexOf(termLower, fromIndex);
			if (matchStart === -1) break;
			const matchEnd = matchStart + termLower.length;
			fromIndex = matchStart + 1; // allow overlapping matches

			// Find the items covered by [matchStart, matchEnd).
			const covered: LineItem[] = line.items.filter(
				li => li.lineStart + li.item.str.length > matchStart && li.lineStart < matchEnd
			);

			for (const li of covered) {
				const itemStartInLine = li.lineStart;
				const itemEndInLine = li.lineStart + li.item.str.length;
				const relStart = Math.max(matchStart, itemStartInLine) - itemStartInLine;
				const relEnd = Math.min(matchEnd, itemEndInLine) - itemStartInLine;
				rects.push(subRect(li.item, relStart, relEnd, viewport));
			}
		}
	}

	return rects;
}
