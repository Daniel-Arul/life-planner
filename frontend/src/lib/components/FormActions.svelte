<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<!-- Button row that sticks to the bottom of a scrolling sheet on phones. -->
<div class="actions">{@render children()}</div>

<style>
	.actions {
		position: sticky;
		bottom: -1rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin: auto -1rem -1rem;
		padding: 0.75rem 1rem 1rem;
		background: var(--color-surface);
		border-top: 2px solid var(--color-ink);
	}
</style>
