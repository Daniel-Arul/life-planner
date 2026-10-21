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

	select {
		appearance: none;
		padding-right: 2rem;
		/* Pixel down-arrow. */
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 7 4' shape-rendering='crispEdges'%3E%3Cpath fill='%232b2a33' d='M0 0h7v1H0zM1 1h5v1H1zM2 2h3v1H2zM3 3h1v1H3z'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 0.75rem center;
		background-size: 0.7rem;
	}
</style>
