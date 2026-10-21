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
	<label class="field-label" for={inputId}>{label}</label>
	<input id={inputId} class="retro-input" bind:value {...rest} />
</div>

<style>
	.field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		min-width: 0;
	}
</style>
