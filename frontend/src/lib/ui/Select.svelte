<script lang="ts" generics="T extends string | number">
	import type { HTMLSelectAttributes } from 'svelte/elements';

	let {
		label,
		value = $bindable(),
		options,
		...rest
	}: Omit<HTMLSelectAttributes, 'value'> & {
		label: string;
		value: T;
		options: readonly { value: T; label: string }[];
	} = $props();

	const id = $props.id();
</script>

<div class="field">
	<label class="field-label" for={id}>{label}</label>
	<select {id} class="retro-input" bind:value {...rest}>
		{#each options as option (option.value)}
			<option value={option.value}>{option.label}</option>
		{/each}
	</select>
</div>

<style>
	.field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		min-width: 0;
	}
</style>
