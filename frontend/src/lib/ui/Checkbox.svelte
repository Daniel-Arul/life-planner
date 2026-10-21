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
	<input type="checkbox" class="retro-check" bind:checked {...rest} />
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
</style>
