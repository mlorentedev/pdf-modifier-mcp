import { describe, expect, it } from 'vitest';
import { computeScrollTarget } from './scroll';

// A typical preview container: 400x600 viewport, scrollable content 1000px tall.
const container = {
	clientWidth: 400,
	clientHeight: 600,
	scrollWidth: 1000,
	scrollHeight: 1400
};

describe('computeScrollTarget', () => {
	it('centers a rect that is below the current viewport', () => {
		// Rect at canvas y=900, height 40. To center: 900 + 20 - 300 = 620.
		const target = computeScrollTarget(
			{ x: 0, y: 900, width: 100, height: 40 },
			container
		);

		expect(target.scrollTop).toBeCloseTo(620);
	});

	it('clamps to 0 when the rect is above the viewport top', () => {
		const target = computeScrollTarget(
			{ x: 0, y: -50, width: 100, height: 40 },
			container
		);

		expect(target.scrollTop).toBe(0);
	});

	it('clamps to the maximum scroll when the rect is near the bottom', () => {
		// max scrollTop = 1400 - 600 = 800
		const target = computeScrollTarget(
			{ x: 0, y: 2000, width: 100, height: 40 },
			container
		);

		expect(target.scrollTop).toBe(800);
	});

	it('scrolls horizontally to bring an off-screen rect into view', () => {
		const target = computeScrollTarget(
			{ x: 900, y: 100, width: 50, height: 40 },
			container
		);

		// max scrollLeft = 1000 - 400 = 600; center target = 900 + 25 - 200 = 725 -> clamp 600
		expect(target.scrollLeft).toBe(600);
	});

	it('clamps to 0 when the centered target would be above the viewport', () => {
		// Rect at y=200: center 220 - 300 = -80 -> clamped to 0.
		const target = computeScrollTarget(
			{ x: 50, y: 200, width: 100, height: 40 },
			container
		);

		expect(target.scrollTop).toBe(0);
		expect(target.scrollLeft).toBe(0);
	});

	it('returns zero scroll for a zero-size container', () => {
		const empty = { clientWidth: 0, clientHeight: 0, scrollWidth: 0, scrollHeight: 0 };
		const target = computeScrollTarget({ x: 0, y: 0, width: 0, height: 0 }, empty);

		expect(target.scrollTop).toBe(0);
		expect(target.scrollLeft).toBe(0);
	});
});
