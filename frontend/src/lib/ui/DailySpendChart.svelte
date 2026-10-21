<script lang="ts">
	import { formatDay, parseLocal } from '$lib/dates';
	import { formatMoney } from '$lib/money';

	let {
		days,
		loading = false,
		onselect
	}: {
		days: { date: string; total_cents: number }[];
		/** Keep the previous render dimmed while new data loads. */
		loading?: boolean;
		onselect?: (date: string) => void;
	} = $props();

	// Layout in CSS pixels, measured from the container.
	const MARGIN = { top: 20, right: 8, bottom: 24, left: 48 };
	const PLOT_HEIGHT = 140;
	const MAX_BAR = 24;

	let width = $state(320);
	let active = $state<number | null>(null);

	const plotWidth = $derived(Math.max(width - MARGIN.left - MARGIN.right, 50));
	const band = $derived(plotWidth / Math.max(days.length, 1));
	// Never fill the slot: cap at 24px and leave at least a 2px gap between bars.
	const barWidth = $derived(Math.max(2, Math.min(MAX_BAR, band - 2)));
	const peak = $derived(Math.max(0, ...days.map((d) => d.total_cents)));
	const yMax = $derived(niceCeil(peak));
	const ticks = $derived([0, yMax / 2, yMax]);
	const peakIndex = $derived(peak > 0 ? days.findIndex((d) => d.total_cents === peak) : -1);

	const y = (cents: number) => MARGIN.top + PLOT_HEIGHT - (cents / yMax) * PLOT_HEIGHT;
	const bandX = (i: number) => MARGIN.left + i * band;

	/** Round up to a clean axis maximum: 1, 2, 2.5 or 5 times a power of ten. */
	function niceCeil(cents: number): number {
		if (cents <= 0) return 1000;
		const magnitude = 10 ** Math.floor(Math.log10(cents));
		const step = [1, 2, 2.5, 5, 10].find((s) => s * magnitude >= cents) ?? 10;
		return step * magnitude;
	}

	function onkeydown(e: KeyboardEvent) {
		if (!days.length) return;
		const current = active ?? -1;
		if (e.key === 'ArrowRight') active = Math.min(days.length - 1, current + 1);
		else if (e.key === 'ArrowLeft') active = Math.max(0, current < 0 ? days.length - 1 : current - 1);
		else if (e.key === 'Enter' && active !== null) onselect?.(days[active].date);
		else return;
		e.preventDefault();
	}

	const activeDay = $derived(active !== null ? days[active] : null);
	const tooltipLeft = $derived(
		active !== null ? Math.min(Math.max(bandX(active) + band / 2, 70), width - 70) : 0
	);
</script>

<div
	class="chart"
	class:loading
	bind:clientWidth={width}
	role="slider"
	aria-label="Spending per day"
	aria-valuemin={1}
	aria-valuemax={days.length}
	aria-valuenow={(active ?? 0) + 1}
	aria-valuetext={activeDay
		? `${formatDay(activeDay.date)}: ${formatMoney(activeDay.total_cents)}`
		: 'Use left and right arrows to read each day'}
	tabindex="0"
	{onkeydown}
	onblur={() => (active = null)}
	onpointerleave={() => (active = null)}
>
	<svg width={width} height={MARGIN.top + PLOT_HEIGHT + MARGIN.bottom} aria-hidden="true">
		<!-- Gridlines + y ticks: hairline, solid, recessive. -->
		{#each ticks as tick (tick)}
			<line
				class="grid"
				class:baseline={tick === 0}
				x1={MARGIN.left}
				x2={width - MARGIN.right}
				y1={y(tick) + 0.5}
				y2={y(tick) + 0.5}
			/>
			<text class="tick tabular" x={MARGIN.left - 6} y={y(tick)} dy="0.32em" text-anchor="end">
				{formatMoney(tick, { compact: true })}
			</text>
		{/each}

		{#each days as day, i (day.date)}
			{#if day.total_cents > 0}
				<rect
					class="bar"
					class:active={active === i}
					x={bandX(i) + (band - barWidth) / 2}
					y={y(day.total_cents)}
					width={barWidth}
					height={Math.max(1, MARGIN.top + PLOT_HEIGHT - y(day.total_cents))}
				/>
			{/if}
			<!-- Hit target: the whole column, bigger than the bar. -->
			<rect
				class="hit"
				role="presentation"
				x={bandX(i)}
				y={MARGIN.top}
				width={band}
				height={PLOT_HEIGHT}
				onpointerenter={() => (active = i)}
				onclick={() => onselect?.(day.date)}
			/>
		{/each}

		<!-- One direct label: the peak day. -->
		{#if peakIndex >= 0 && active === null}
			<text
				class="peak tabular"
				x={bandX(peakIndex) + band / 2}
				y={y(peak) - 6}
				text-anchor={peakIndex < 3 ? 'start' : peakIndex > days.length - 4 ? 'end' : 'middle'}
			>
				{formatMoney(peak, { compact: true })}
			</text>
		{/if}

		<!-- Weekly day-of-month labels. -->
		{#each days as day, i (day.date)}
			{#if i % 7 === 0}
				<text class="tick tabular" x={bandX(i) + band / 2} y={MARGIN.top + PLOT_HEIGHT + 16} text-anchor="middle">
					{parseLocal(day.date).getDate()}
				</text>
			{/if}
		{/each}
	</svg>

	{#if activeDay}
		<div class="tooltip" style:left="{tooltipLeft}px" aria-hidden="true">
			<strong class="tabular">{formatMoney(activeDay.total_cents)}</strong>
			<span>{formatDay(activeDay.date)}</span>
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

	svg {
		display: block;
		overflow: visible;
	}

	.chart:focus-visible {
		outline: 2px dashed var(--color-ink);
		outline-offset: 4px;
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
		fill: var(--color-peach-deep);
	}

	.bar.active {
		fill: color-mix(in srgb, var(--color-peach-deep) 70%, var(--color-ink));
	}

	.hit {
		fill: transparent;
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
