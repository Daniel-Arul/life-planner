<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	let {
		label,
		value = $bindable(''),
		id,
		...rest
	}: HTMLInputAttributes & { label: string; value?: string } = $props();

	const uid = $props.id();
	const inputId = $derived(id ?? uid);
</script>

<div class="field">
	<label for={inputId}>{label}</label>
	<input id={inputId} bind:value {...rest} />
</div>

<style>
	.field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	label {
		font-family: var(--font-pixel);
		font-size: 0.9rem;
	}

	input {
		min-height: 44px;
		padding: 0.5rem 0.75rem;
		font: inherit;
		font-size: 1rem; /* 16px stops iOS zooming on focus */
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		border-radius: 0;
		/* Inset bevel: the field looks pressed into the window. */
		box-shadow: inset 2px 2px 0 color-mix(in srgb, var(--color-ink) 15%, transparent);
		caret-color: var(--color-ink);
		caret-shape: block;
	}

	input:focus-visible {
		outline: none;
		background: color-mix(in srgb, var(--color-butter) 35%, var(--color-surface));
	}

	input::placeholder {
		color: var(--color-muted);
	}
</style>
