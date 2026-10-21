<script lang="ts">
	import type { EventColor } from '$lib/types';

	const COLORS: EventColor[] = ['lavender', 'mint', 'peach', 'butter', 'sky', 'rose'];

	let { label, value = $bindable() }: { label: string; value: EventColor } = $props();
</script>

<fieldset>
	<legend class="field-label">{label}</legend>
	<div class="swatches">
		{#each COLORS as color (color)}
			<label class="swatch" style:--swatch="var(--color-{color})" title={color}>
				<input type="radio" name="color" value={color} bind:group={value} />
				<span class="sr-only">{color}</span>
			</label>
		{/each}
	</div>
</fieldset>

<style>
	fieldset {
		margin: 0;
		padding: 0;
		border: 0;
	}

	legend {
		padding: 0;
		margin-bottom: 0.25rem;
	}

	.swatches {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.swatch {
		position: relative;
		width: 44px;
		height: 44px;
		background: var(--swatch);
		border: 2px solid var(--color-ink);
		cursor: pointer;
	}

	input {
		position: absolute;
		inset: 0;
		margin: 0;
		opacity: 0;
		cursor: pointer;
	}

	/* Selected swatch gets an inner ink square, like a pressed key. */
	.swatch:has(input:checked)::after {
		content: '';
		position: absolute;
		inset: 10px;
		background: var(--color-ink);
	}

	.swatch:has(input:focus-visible) {
		outline: 2px dashed var(--color-ink);
		outline-offset: 3px;
	}
</style>
