// Shared scale helpers and types for the hand-built SVG charts.

export type Column = {
	key: string;
	value: number;
	/** Shown in the tooltip and to screen readers, e.g. "Tue, Oct 21". */
	label: string;
	/** Short x-axis label; only shown where the chart's `showTick` says so. */
	tick: string;
};

/** A clean step (1, 2, 2.5 or 5 times a power of ten) at least `raw` long. */
export function niceStep(raw: number): number {
	if (raw <= 0) return 1;
	const magnitude = 10 ** Math.floor(Math.log10(raw));
	const step = [1, 2, 2.5, 5, 10].find((s) => s * magnitude >= raw - 1e-9) ?? 10;
	return step * magnitude;
}

/**
 * Evenly spaced, round ticks covering [min, max] in about `count` steps.
 * Pass `integer` for counts (no 0.5 workouts).
 */
export function niceTicks(min: number, max: number, count = 2, integer = false): number[] {
	if (max <= min) max = min + (integer ? 1 : 1);
	let step = niceStep((max - min) / count);
	if (integer) step = Math.max(1, Math.ceil(step));
	const start = Math.floor(min / step) * step;
	const end = Math.ceil(max / step) * step;
	const ticks: number[] = [];
	for (let v = start; v <= end + step / 2; v += step) ticks.push(Number(v.toFixed(6)));
	return ticks;
}
