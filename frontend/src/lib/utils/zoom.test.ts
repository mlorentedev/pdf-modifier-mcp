import { describe, expect, it } from 'vitest';
import { computeMaxScale, HARD_MAX_SCALE } from './zoom';

describe('computeMaxScale', () => {
	it('limits scale so canvas pixels never exceed the physical screen width', () => {
		// 1920 CSS px at dpr 1, A4-ish page 612pt wide at scale 1.
		const max = computeMaxScale({ pageWidth: 612, screenWidth: 1920, devicePixelRatio: 1 });
		expect(max).toBeCloseTo(1920 / 612); // ~3.14
		expect(max).toBeLessThanOrEqual(HARD_MAX_SCALE);
	});

	it('accounts for devicePixelRatio (retina has more physical pixels)', () => {
		// 1000 CSS px at dpr 2 -> 2000 physical px (below the hard cap).
		const max = computeMaxScale({ pageWidth: 612, screenWidth: 1000, devicePixelRatio: 2 });
		expect(max).toBeCloseTo((1000 * 2) / 612);
		expect(max).toBeLessThan(HARD_MAX_SCALE);
	});

	it('clamps to the hard max on very high resolution screens', () => {
		const max = computeMaxScale({ pageWidth: 612, screenWidth: 3840, devicePixelRatio: 1 });
		expect(max).toBe(HARD_MAX_SCALE);
	});

	it('never allows less than 1x zoom (readability floor)', () => {
		// Tiny screen vs large page: formula would give < 1; floor at 1.
		const max = computeMaxScale({ pageWidth: 2000, screenWidth: 800, devicePixelRatio: 1 });
		expect(max).toBeGreaterThanOrEqual(1);
	});

	it('scales the limit down for wide pages (large formats)', () => {
		// A0-ish page 2384pt on a 1920 screen: raw formula gives < 1, clamped to
		// the 1x readability floor.
		const max = computeMaxScale({ pageWidth: 2384, screenWidth: 1920, devicePixelRatio: 1 });
		expect(max).toBe(1);
		expect(max).toBeLessThan(HARD_MAX_SCALE);
	});

	it('mobile: narrow screen at dpr 3 keeps a modest zoom ceiling', () => {
		const max = computeMaxScale({ pageWidth: 612, screenWidth: 390, devicePixelRatio: 3 });
		expect(max).toBeCloseTo((390 * 3) / 612);
		expect(max).toBeLessThan(2.5);
	});
});
