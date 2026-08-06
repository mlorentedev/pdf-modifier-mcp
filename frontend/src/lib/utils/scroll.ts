/* Pure helper for computing how far a scroll container must move to bring a
 * given rect (in canvas coordinates) into view. Framework-free so it can be
 * unit-tested without a browser or DOM.
 */

export interface Rect {
	x: number;
	y: number;
	width: number;
	height: number;
}

export interface ScrollContainer {
	clientWidth: number;
	clientHeight: number;
	scrollWidth: number;
	scrollHeight: number;
}

export interface ScrollTarget {
	scrollTop: number;
	scrollLeft: number;
}

function clamp(value: number, min: number, max: number): number {
	return Math.min(Math.max(value, min), max);
}

/**
 * Compute the scroll offsets that center the given rect in the container's
 * viewport, clamped to the scrollable range. Returns zeros for a degenerate
 * (zero-size) container or when the rect is already visible and centered.
 */
export function computeScrollTarget(rect: Rect, container: ScrollContainer): ScrollTarget {
	if (container.clientWidth <= 0 || container.clientHeight <= 0) {
		return { scrollTop: 0, scrollLeft: 0 };
	}

	const maxTop = Math.max(0, container.scrollHeight - container.clientHeight);
	const maxLeft = Math.max(0, container.scrollWidth - container.clientWidth);

	const centerY = rect.y + rect.height / 2;
	const centerX = rect.x + rect.width / 2;

	return {
		scrollTop: clamp(centerY - container.clientHeight / 2, 0, maxTop),
		scrollLeft: clamp(centerX - container.clientWidth / 2, 0, maxLeft)
	};
}
