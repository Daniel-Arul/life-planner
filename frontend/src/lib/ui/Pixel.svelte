<script lang="ts">
	import type { PixelArt } from './icons';

	let { art, size = 24, label }: { art: PixelArt; size?: number; label?: string } = $props();

	const width = $derived(Math.max(...art.map((row) => row.length)));
	const d = $derived(
		art
			.flatMap((row, y) => [...row].map((ch, x) => (ch === '#' ? `M${x} ${y}h1v1h-1z` : '')))
			.join('')
	);
</script>

<svg
	viewBox="0 0 {width} {art.length}"
	width={size}
	height={(size * art.length) / width}
	fill="currentColor"
	shape-rendering="crispEdges"
	role={label ? 'img' : undefined}
	aria-label={label}
	aria-hidden={label ? undefined : 'true'}
>
	<path {d} />
</svg>

<style>
	svg {
		display: inline-block;
		flex-shrink: 0;
	}
</style>
