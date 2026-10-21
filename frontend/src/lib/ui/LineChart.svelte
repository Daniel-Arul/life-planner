<script lang="ts">
	import { niceTicks } from '$lib/charts';
	import { formatDay, parseLocal } from '$lib/dates';

	let {
		points,
		formatValue,
		label,
		color = 'var(--color-mint-deep)',
		onselect
	}: {
		/** Oldest first; dates as "YYYY-MM-DD". */
		points: { date: string; value: number; key: string }[];
		formatValue: (v: number) => string;
		/** Accessible name, e.g. "Bench press, best weight". */
		label: string;
		color?: string;
		onselect?: (key: string) => void;
	} = $props();

	const MARGIN = { top: 22, right: 16, bottom: 24, left: 52 };
	const PLOT_HEIGHT = 160;

	let width = $state(320);
	let active = $state<number | null>(null);

	const plotWidth = $derived(Math.max(width - MARGIN.left - MARGIN.right, 50));
	const times = $derived(points.map((p) => parseLocal(p.date).getTime()));
	const tMin = $derived(Math.min(...times));
	const tMax = $derived(Math.max(...times));
	const values = $derived(points.map((p) => p.value));
	// Progress lines don't need a zero baseline; frame the actual range.
	const ticks = $derived(niceTicks(Math.min(...values), Math.max(...values), 3));
	const yMin = $derived(ticks[0] ?? 0);
	const yMax = $derived(ticks.at(-1) ?? 1);

	const x = (i: number) =>
		tMax === tMin
			? MARGIN.left + plotWidth / 2
			: MARGIN.left + ((times[i] - tMin) / (tMax - tMin)) * plotWidth;
	const y = (v: number) =>
		MARGIN.top + PLOT_HEIGHT - ((v - yMin) / (yMax - yMin || 1)) * PLOT_HEIGHT;

	const path = $derived(points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.value)}`).join(''));
	const activePoint = $derived(active !== null ? points[active] : null);
	const last = $derived(points.length - 1);

	// Date ticks: first, last, and up to two in between.
	const dateTicks = $derived.by(() => {
		if (points.length <= 2) return points.map((_, i) => i);
		const step = Math.max(1, Math.round(last / 3));
		const idx = new Set([0, last]);
		for (let i = step; i < last - step / 2; i += step) idx.add(i);
		return [...idx].sort((a, b) => a - b);
	});

	/** The crosshair finds the X: snap to the nearest point. */
	function onpointermove(e: PointerEvent) {
		const box = (e.currentTarget as HTMLElement).getBoundingClientRect();
		const px = e.clientX - box.left;
		let best = 0;
		for (let i = 1; i < points.length; i++) {
			if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i;
		}
		active = best;
	}

	function onkeydown(e: KeyboardEvent) {
		if (!points.length) return;
		const current = active ?? points.length;
		if (e.key === 'ArrowRight') active = Math.min(last, (active ?? -1) + 1);
		else if (e.key === 'ArrowLeft') active = Math.max(0, current - 1);
		else if (e.key === 'Enter' && active !== null) onselect?.(points[active].key);
		else return;
		e.preventDefault();
	}

	const short = (date: string) =>
		parseLocal(date).toLocaleDateString([], { month: 'short', day: 'numeric' });
</script>

<div
	class="chart"
	style:--mark={color}
	bind:clientWidth={width}
	role="slider"
	aria-label={label}
	aria-valuemin={1}
	aria-valuemax={points.length}
	aria-valuenow={(active ?? last) + 1}
	aria-valuetext={activePoint
		? `${formatDay(activePoint.date)}: ${formatValue(activePoint.value)}`
		: 'Use left and right arrows to read each session'}
	tabindex="0"
	{onkeydown}
	{onpointermove}
	onpointerleave={() => (active = null)}
	onblur={() => (active = null)}
	onclick={() => active !== null && onselect?.(points[active].key)}
>
	<svg width={width} height={MARGIN.top + PLOT_HEIGHT + MARGIN.bottom} aria-hidden="true">
		{#each ticks as t (t)}
			<line class="grid" x1={MARGIN.left} x2={width - MARGIN.right} y1={y(t) + 0.5} y2={y(t) + 0.5} />
			<text class="tick tabular" x={MARGIN.left - 6} y={y(t)} dy="0.32em" text-anchor="end">
				{formatValue(t)}
			</text>
		{/each}
		{#each dateTicks as i (i)}
			<text
				class="tick tabular"
				x={x(i)}
				y={MARGIN.top + PLOT_HEIGHT + 16}
				text-anchor={i === 0 ? 'start' : i === last ? 'end' : 'middle'}
			>
				{short(points[i].date)}
			</text>
		{/each}

		{#if activePoint && active !== null}
			<line class="crosshair" x1={x(active)} x2={x(active)} y1={MARGIN.top} y2={MARGIN.top + PLOT_HEIGHT} />
		{/if}

		<path class="line" d={path} />
		{#each points as p, i (p.key)}
			<circle class="dot" class:active={active === i} cx={x(i)} cy={y(p.value)} r={active === i ? 6 : 4} />
		{/each}

		<!-- Direct label on the latest value. -->
		{#if active === null && points.length}
			<text class="end-label tabular" x={x(last)} y={y(points[last].value) - 10} text-anchor={points.length > 1 ? 'end' : 'middle'}>
				{formatValue(points[last].value)}
			</text>
		{/if}
	</svg>

	{#if activePoint && active !== null}
		<div
			class="tooltip"
			style:left="{Math.min(Math.max(x(active), 70), width - 70)}px"
			aria-hidden="true"
		>
			<strong class="tabular">{formatValue(activePoint.value)}</strong>
			<span>{formatDay(activePoint.date)}</span>
		</div>
	{/if}
</div>

<style>
	.chart {
		position: relative;
		cursor: crosshair;
		touch-action: pan-y;
	}

	.chart:focus-visible {
		outline: 2px dashed var(--color-ink);
		outline-offset: 4px;
	}

	svg {
		display: block;
		overflow: visible;
	}

	.grid {
		stroke: color-mix(in srgb, var(--color-ink) 12%, transparent);
		stroke-width: 1;
	}

	.tick {
		font-size: 11px;
		fill: var(--color-muted);
	}

	.crosshair {
		stroke: color-mix(in srgb, var(--color-ink) 45%, transparent);
		stroke-width: 1;
	}

	.line {
		fill: none;
		stroke: var(--mark);
		stroke-width: 2;
		stroke-linejoin: round;
		stroke-linecap: round;
	}

	/* Markers: >= 8px, with a 2px surface ring so they read where they cross the line. */
	.dot {
		fill: var(--mark);
		stroke: var(--color-surface);
		stroke-width: 2;
	}

	.end-label {
		font-size: 12px;
		font-weight: 600;
		fill: var(--color-ink);
	}

	.tooltip {
		position: absolute;
		top: -0.5rem;
		transform: translate(-50%, -100%);
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.25rem 0.6rem;
		font-size: 0.8rem;
		white-space: nowrap;
		pointer-events: none;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
	}

	.tooltip strong {
		font-size: 0.95rem;
	}

	.tooltip span {
		color: var(--color-muted);
	}
</style>
