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

/**
 * Compute canvas-space highlight rectangles for every text item whose
 * string contains the search term (case-insensitive). Returns an empty
 * array when the term or items are empty.
 */
export function getHighlightRects(
	term: string,
	items: HighlightTextItem[],
	viewport: HighlightViewport
): HighlightRect[] {
	const trimmed = term.trim();
	if (!trimmed) return [];

	const termLower = trimmed.toLowerCase();
	const rects: HighlightRect[] = [];

	for (const item of items) {
		if (!item.str) continue;
		if (!item.str.toLowerCase().includes(termLower)) continue;

		const tx = transform(viewport.transform, item.transform);
		const width = item.width * viewport.scale;
		const height = item.height * viewport.scale;
		const x = tx[4];
		const y = tx[5] - height;

		rects.push({ x, y, width: Math.max(0, width), height: Math.max(0, height) });
	}

	return rects;
}