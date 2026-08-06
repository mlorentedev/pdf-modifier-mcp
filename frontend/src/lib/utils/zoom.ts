/* Pure helper for computing the maximum zoom scale of the PDF preview.
 * Framework-free so it can be unit-tested without a browser.
 *
 * Why a dynamic limit: the preview canvas is rendered at page_width × scale
 * physical pixels. Zooming beyond the physical pixel resolution of the screen
 * adds no detail — the browser must downscale the oversized canvas, which
 * produces blurry/distorted text. The ceiling is therefore the scale at which
 * one canvas pixel equals one physical screen pixel.
 */

/** Absolute hard cap regardless of screen size (sanity bound). */
export const HARD_MAX_SCALE = 4;

/** Never allow less than 1x zoom (readability floor). */
const MIN_SCALE = 1;

export interface MaxScaleParams {
	/** Page width in PDF points at scale 1. */
	pageWidth: number;
	/** Screen width in CSS pixels (window.screen.width). */
	screenWidth: number;
	/** Device pixel ratio (window.devicePixelRatio). */
	devicePixelRatio: number;
	/** Hard cap to clamp to (defaults to HARD_MAX_SCALE). */
	hardMax?: number;
}

/**
 * Compute the maximum useful zoom scale: page rendered at this scale fills the
 * physical screen width (screenWidth × dpr) one-to-one. Clamped to
 * [MIN_SCALE, hardMax].
 */
export function computeMaxScale({
	pageWidth,
	screenWidth,
	devicePixelRatio,
	hardMax = HARD_MAX_SCALE
}: MaxScaleParams): number {
	if (pageWidth <= 0 || screenWidth <= 0) return MIN_SCALE;

	const physicalPixels = screenWidth * devicePixelRatio;
	const scale = physicalPixels / pageWidth;
	return Math.min(hardMax, Math.max(MIN_SCALE, scale));
}
