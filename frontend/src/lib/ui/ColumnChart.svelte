<script lang="ts">
	import { niceTicks, type Column } from '$lib/charts';

	let {
		columns,
		formatValue,
		formatTick = formatValue,
		label,
		color = 'var(--color-peach-deep)',
		integer = false,
		showTick = (i: number) => i % 7 === 0,
		loading = false,
		onselect
	}: {
		columns: Column[];
		formatValue: (v: number) => string;
		/** Compact formatter for y-axis ticks and the peak label. */
		formatTick?: (v: number) => string;
		/** Accessible name, e.g. "Spending per day". */
		label: string;
		color?: string;
		/** Values are counts: keep ticks on whole numbers. */
		integer?: boolean;
		showTick?: (i: number) => boolean;
		/** Keep the previous render dimmed while new data loads. */
		loading?: boolean;
		onselect?: (key: string) => void;
	} = $props();

	// Layout in CSS pixels, measured from the container.
	const MARGIN = { top: 20, right: 8, bottom: 24, left: 48 };
	const PLOT_HEIGHT = 140;
	const MAX_BAR = 24;

	let width = $state(320);
	let active = $state<number | null>(null);

	const plotWidth = $derived(Math.max(width - MARGIN.left - MARGIN.right, 50));
	const band = $derived(plotWidth / Math.max(columns.length, 1));
	// Never fill the slot: cap at 24px and leave at least a 2px gap between bars.
	const barWidth = $derived(Math.max(2, Math.min(MAX_BAR, band - 2)));
	const peak = $derived(Math.max(0, ...columns.map((c) => c.value)));
	const ticks = $derived(niceTicks(0, peak || (integer ? 2 : 1), 2, integer));
	const yMax = $derived(ticks.at(-1) ?? 1);
	const peakIndex = $derived(peak > 0 ? columns.findIndex((c) => c.value === peak) : -1);
	const activeColumn = $derived(active !== null ? columns[active] : null);

	const y = (v: number) => MARGIN.top + PLOT_HEIGHT - (v / yMax) * PLOT_HEIGHT;
	const bandX = (i: number) => MARGIN.left + i * band;

	const tooltipLeft = $derived(
		active !== null ? Math.min(Math.max(bandX(active) + band / 2, 70), width - 70) : 0
	);

	function onkeydown(e: KeyboardEvent) {
		if (!columns.length) return;
		const current = active ?? -1;
		if (e.key === 'ArrowRight') active = Math.min(columns.length - 1, current + 1);
		else if (e.key === 'ArrowLeft') active = Math.max(0, current < 0 ? columns.length - 1 : current - 1);
		else if (e.key === 'Enter' && active !== null) onselect?.(columns[active].key);
		else return;
		e.preventDefault();
	}
</script>

<div
	class="chart"
	class:loading
	style:--mark={color}
	bind:clientWidth={width}
	role="slider"
	aria-label={label}
	aria-valuemin={1}
	aria-valuemax={columns.length}
	aria-valuenow={(active ?? 0) + 1}
	aria-valuetext={activeColumn
		? `${activeColumn.label}: ${formatValue(activeColumn.value)}`
		: 'Use left and right arrows to read each value'}
	tabindex="0"
	{onkeydown}
	onblur={() => (active = null)}
	onpointerleave={() => (active = null)}
>
	<svg width={width} height={MARGIN.top + PLOT_HEIGHT + MARGIN.bottom} aria-hidden="true">
		<!-- Gridlines + y ticks: hairline, solid, recessive. -->
		{#each ticks as t (t)}
			<line
				class="grid"
				class:baseline={t === 0}
				x1={MARGIN.left}
				x2={width - MARGIN.right}
				y1={y(t) + 0.5}
				y2={y(t) + 0.5}
			/>
			<text class="tick tabular" x={MARGIN.left - 6} y={y(t)} dy="0.32em" text-anchor="end">
				{formatTick(t)}
			</text>
		{/each}

		{#each columns as column, i (column.key)}
			{#if column.value > 0}
				<rect
					class="bar"
					class:active={active === i}
					x={bandX(i) + (band - barWidth) / 2}
					y={y(column.value)}
					width={barWidth}
					height={Math.max(1, MARGIN.top + PLOT_HEIGHT - y(column.value))}
				/>
			{/if}
			<!-- Hit target: the whole column, bigger than the bar. -->
			<rect
				class="hit"
				class:clickable={!!onselect}
				role="presentation"
				x={bandX(i)}
				y={MARGIN.top}
				width={band}
				height={PLOT_HEIGHT}
				onpointerenter={() => (active = i)}
				onclick={() => onselect?.(column.key)}
			/>
			{#if showTick(i)}
				<text class="tick tabular" x={bandX(i) + band / 2} y={MARGIN.top + PLOT_HEIGHT + 16} text-anchor="middle">
					{column.tick}
				</text>
			{/if}
		{/each}

		<!-- One direct label: the peak. -->
		{#if peakIndex >= 0 && active === null}
			<text
				class="peak tabular"
				x={bandX(peakIndex) + band / 2}
				y={y(peak) - 6}
				text-anchor={peakIndex < 2 ? 'start' : peakIndex > columns.length - 3 ? 'end' : 'middle'}
			>
				{formatTick(peak)}
			</text>
		{/if}
	</svg>

	{#if activeColumn}
		<div class="tooltip" style:left="{tooltipLeft}px" aria-hidden="true">
			<strong class="tabular">{formatValue(activeColumn.value)}</strong>
			<span>{activeColumn.label}</span>
		</div>
	{/if}
</div>

<style>
	.chart {
		position: relative;
		transition: opacity 150ms;
	}

	.chart.loading {
		opacity: 0.5;
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

	.grid.baseline {
		stroke: color-mix(in srgb, var(--color-ink) 45%, transparent);
	}

	.tick {
		font-size: 11px;
		fill: var(--color-muted);
	}

	.bar {
		fill: var(--mark);
	}

	.bar.active {
		fill: color-mix(in srgb, var(--mark) 70%, var(--color-ink));
	}

	.hit {
		fill: transparent;
	}

	.hit.clickable {
		cursor: pointer;
	}

	.peak {
		font-size: 11px;
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
