/* Pure helpers for grouping raw PDF text spans into semantic entries.
 * Framework-free so they can be unit-tested without a browser.
 *
 * The backend `get_structure` API returns one TextElement per PyMuPDF span,
 * so a visual "Hello World" line arrives as several spans. Real-world PDFs
 * fragment text further:
 *   - explicit space spans (" " between words, e.g. PyMuPDF dict mode)
 *   - Type3 fonts: each glyph/fragment has its own resource name
 *     ("Type3 (16 0 R)" vs "Type3 (17 0 R)") so font identity is unreliable
 *   - style changes mid-word (bold runs, subset font names)
 *
 * This module merges consecutive spans that belong to the same visual run
 * into one ElementGroup for the sidebar, without touching the API contract
 * (display-only).
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

/** Preview navigation target: which page to show and where to scroll. */
export interface FocusTarget {
	page: number;
	bbox: [number, number, number, number];
}

/**
 * Strong-merge gap factor: spans closer than this (× font size) are treated
 * as part of the same word/visual run even when font/size differ (Type3
 * fragment names, style runs). Column gutters are much wider than this.
 */
export const STRONG_GAP_FACTOR = 0.5;

/**
 * Weak-merge gap factor: spans closer than this (× font size) with the same
 * font + size belong to the same visual line (normal inter-word spacing).
 */
export const WEAK_GAP_FACTOR = 1.2;

/** Baseline tolerance (PDF points) for spans on the same visual line. */
const BASELINE_EPSILON = 0.5;

/**
 * Minimum horizontal gap (PDF points) to render a space between joined spans.
 * Absorbs float jitter from PyMuPDF bboxes (~1e-5 pt) on tightly packed glyph
 * runs (Type3 fragments) while still separating real word gaps (~2-5 pt).
 */
const JOIN_SPACE_EPSILON = 0.5;

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

function isWhitespace(s: TextElement): boolean {
	return s.text.trim().length === 0;
}

/**
 * Join the spans of a group into a single display string. Space is inserted
 * only where a real gap exists: between spans separated horizontally, or at
 * explicit whitespace spans. Contiguous fragments (gap ≤ 0, e.g. Type3 glyph
 * runs) join without a separator.
 */
function joinText(spans: TextElement[]): string {
	let text = '';
	let prev: TextElement | null = null;

	for (const s of spans) {
		if (isWhitespace(s)) {
			// Normalize any explicit whitespace span to a single space.
			if (text && !text.endsWith(' ')) text += ' ';
			prev = s;
			continue;
		}
		if (text && prev) {
			const prevIsWhitespace = isWhitespace(prev);
			const gap = gapBetween(prev, s);
			if (!prevIsWhitespace && gap > JOIN_SPACE_EPSILON) text += ' ';
		}
		text += s.text;
		prev = s;
	}

	// Trim stray leading/trailing whitespace left by boundary space spans.
	return text.trim();
}

function mergeGroup(spans: TextElement[]): ElementGroup {
	const first = spans[0];
	const last = spans[spans.length - 1];

	// Bbox should span only visible text: skip leading/trailing whitespace
	// spans so click-to-locate targets the words, not a stray space.
	const visible = spans.filter(s => !isWhitespace(s));
	const firstVisible = visible[0] ?? first;
	const lastVisible = visible[visible.length - 1] ?? last;

	return {
		text: joinText(spans),
		bbox: [firstVisible.bbox[0], firstVisible.bbox[1], lastVisible.bbox[2], lastVisible.bbox[3]],
		origin: [...first.origin],
		font: first.font,
		size: first.size,
		color: first.color,
		elements: spans
	};
}

/**
 * Can two consecutive spans be merged into the same visual run?
 *
 * Strong rule (geometric): same baseline + small gap → merge regardless of
 * font/size. This recovers Type3 fragments whose resource names differ
 * ("Type3 (16 0 R)" + "Type3 (17 0 R)" are the same visual font) and
 * mid-word style runs.
 *
 * Weak rule (stylistic): same baseline + same font/size + moderate gap →
 * merge (normal inter-word spacing within a line).
 *
 * Anything wider than WEAK_GAP_FACTOR (e.g. column gutters) splits groups.
 */
function canMerge(prev: TextElement, next: TextElement): boolean {
	if (!sameBaseline(prev, next)) return false;

	const gap = gapBetween(prev, next);
	const size = Math.max(prev.size, next.size);

	if (gap <= STRONG_GAP_FACTOR * size) return true;
	if (sameStyle(prev, next) && gap <= WEAK_GAP_FACTOR * size) return true;
	return false;
}

/**
 * Group consecutive text spans into semantic runs (see module docstring for
 * the merge rules).
 */
export function groupElements(elements: TextElement[]): ElementGroup[] {
	if (elements.length === 0) return [];

	const groups: ElementGroup[] = [];
	let current: TextElement[] = [elements[0]];

	for (let i = 1; i < elements.length; i++) {
		const prev = elements[i - 1];
		const next = elements[i];

		if (canMerge(prev, next)) {
			current.push(next);
		} else {
			groups.push(mergeGroup(current));
			current = [next];
		}
	}
	groups.push(mergeGroup(current));

	return groups;
}
