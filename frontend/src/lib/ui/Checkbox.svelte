<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	let {
		checked = $bindable(false),
		children,
		...rest
	}: HTMLInputAttributes & { checked?: boolean; children: Snippet } = $props();
</script>

<label class="checkbox">
	<input type="checkbox" bind:checked {...rest} />
	<span>{@render children()}</span>
</label>

<style>
	.checkbox {
		display: inline-flex;
		align-items: center;
		gap: 0.6rem;
		min-height: 44px;
		cursor: pointer;
	}

	input {
		appearance: none;
		flex-shrink: 0;
		width: 1.4rem;
		height: 1.4rem;
		margin: 0;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		border-radius: 0;
		box-shadow: inset 2px 2px 0 color-mix(in srgb, var(--color-ink) 15%, transparent);
		cursor: pointer;
	}

	input:checked {
		background-color: var(--color-butter);
		/* Pixel checkmark. */
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8' shape-rendering='crispEdges'%3E%3Cpath fill='%232b2a33' d='M1 3h1v1H1zM2 4h1v1H2zM3 5h1v1H3zM4 4h1v1H4zM5 3h1v1H5zM6 2h1v1H6z'/%3E%3C/svg%3E");
		background-size: 100%;
		box-shadow: none;
	}
</style>
