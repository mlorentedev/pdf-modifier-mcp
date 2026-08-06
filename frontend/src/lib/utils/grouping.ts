/* Pure helpers for grouping raw PDF text spans into semantic entries.
 * Framework-free so they can be unit-tested without a browser.
 *
 * The backend `get_structure` API returns one TextElement per PyMuPDF span,
 * so a visual "Hello World" line arrives as two spans ("Hello", "World").
 * This module merges consecutive spans that belong to the same visual word
 * run into one ElementGroup for the sidebar, without touching the API
 * contract (display-only).
 */

export interface TextElement {
	text: string;
	bbox: [number, number, number, number];
	origin: [number, number];
	font: string;
	size: number;
	color: number;
}

export interface ElementGroup {
	text: string;
	bbox: [number, number, number, number];
	origin: [number, number];
	font: string;
	size: number;
	color: number;
	/** The individual spans that make up this group (for highlight/locate). */
	elements: TextElement[];
}

/**
 * Maximum gap (as a multiple of the font size) allowed between consecutive
 * spans on the same baseline to consider them part of the same visual run.
 * 1.2× was validated against single-line + two-column layouts: a threshold
 * this small keeps column gutters (usually several × font size) unmerged.
 */
export const MAX_GAP_FACTOR = 1.2;

/** Baseline tolerance (PDF points) for spans on the same visual line. */
const BASELINE_EPSILON = 0.5;

function sameBaseline(a: TextElement, b: TextElement): boolean {
	return Math.abs(a.origin[1] - b.origin[1]) <= BASELINE_EPSILON;
}

function sameStyle(a: TextElement, b: TextElement): boolean {
	return a.font === b.font && Math.abs(a.size - b.size) <= 0.01;
}

function gapBetween(prev: TextElement, next: TextElement): number {
	// Horizontal gap = next left edge minus prev right edge (positive = separated).
	return next.bbox[0] - prev.bbox[2];
}

function mergeGroup(spans: TextElement[]): ElementGroup {
	const first = spans[0];
	const last = spans[spans.length - 1];
	return {
		text: spans.map(s => s.text).join(' '),
		bbox: [first.bbox[0], first.bbox[1], last.bbox[2], last.bbox[3]],
		origin: [...first.origin],
		font: first.font,
		size: first.size,
		color: first.color,
		elements: spans
	};
}

/**
 * Group consecutive text spans into semantic runs.
 *
 * Two spans are merged when they appear in order, share a baseline (within a
 * float tolerance), share font + size, and the horizontal gap between them is
 * at most `MAX_GAP_FACTOR × font size`. Anything else starts a new group.
 */
export function groupElements(elements: TextElement[]): ElementGroup[] {
	if (elements.length === 0) return [];

	const groups: ElementGroup[] = [];
	let current: TextElement[] = [elements[0]];

	for (let i = 1; i < elements.length; i++) {
		const prev = elements[i - 1];
		const next = elements[i];

		const canMerge =
			sameBaseline(prev, next) &&
			sameStyle(prev, next) &&
			gapBetween(prev, next) <= MAX_GAP_FACTOR * prev.size;

		if (canMerge) {
			current.push(next);
		} else {
			groups.push(mergeGroup(current));
			current = [next];
		}
	}
	groups.push(mergeGroup(current));

	return groups;
}
