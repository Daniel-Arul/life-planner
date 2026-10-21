<script lang="ts">
	import type { HTMLTextareaAttributes } from 'svelte/elements';

	let {
		label,
		value = $bindable(''),
		rows = 3,
		...rest
	}: HTMLTextareaAttributes & { label: string; value?: string } = $props();

	const id = $props.id();
</script>

<div class="field">
	<label class="field-label" for={id}>{label}</label>
	<textarea {id} class="retro-input" {rows} bind:value {...rest}></textarea>
</div>

<style>
	.field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	textarea {
		resize: vertical;
	}
</style>
