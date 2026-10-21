<script lang="ts">
	let { label, value, note }: { label: string; value: string; note?: string } = $props();
</script>

<!-- Stat tile: label, value (proportional figures), optional note. -->
<div class="tile">
	<span class="label">{label}</span>
	<span class="value">{value}</span>
	{#if note}<span class="note">{note}</span>{/if}
</div>

<style>
	.tile {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		min-width: 0;
		padding: 0.6rem 0.8rem;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
	}

	.label {
		font-family: var(--font-pixel);
		font-size: 0.85rem;
		color: var(--color-muted);
	}

	.value {
		font-size: 1.9rem;
		font-weight: 600;
		line-height: 1.15;
	}

	.note {
		font-size: 0.8rem;
		color: var(--color-muted);
	}
</style>
