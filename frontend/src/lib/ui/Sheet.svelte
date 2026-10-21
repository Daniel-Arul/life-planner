<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { Accent } from '$lib/modules';
	import Window from './Window.svelte';

	let {
		open,
		title,
		accent = 'lavender',
		onclose,
		children
	}: {
		open: boolean;
		title: string;
		accent?: Accent;
		onclose: () => void;
		children: Snippet;
	} = $props();

	let dialog: HTMLDialogElement | undefined = $state();

	// A native modal <dialog> gives us focus trapping, Esc to close and inert background.
	$effect(() => {
		if (!dialog) return;
		if (open && !dialog.open) dialog.showModal();
		else if (!open && dialog.open) dialog.close();
	});
</script>

<dialog
	bind:this={dialog}
	onclose={onclose}
	onclick={(e) => {
		// Clicking the backdrop (the dialog element itself) closes it.
		if (e.target === dialog) onclose();
	}}
>
	{#if open}
		<Window {title} {accent} fill>
			{#snippet actions()}
				<button type="button" class="close" aria-label="Close" onclick={onclose}>×</button>
			{/snippet}
			{@render children()}
		</Window>
	{/if}
</dialog>

<style>
	/* Phone: full-screen sheet. */
	dialog {
		box-sizing: border-box;
		width: 100%;
		max-width: none;
		height: 100dvh;
		max-height: none;
		margin: 0;
		padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom)
			env(safe-area-inset-left);
		border: 0;
		background: var(--color-paper);
		color: inherit;
	}

	dialog::backdrop {
		/* 50% dither, like a classic Mac modal. */
		background-color: rgb(43 42 51 / 0.25);
		background-image: repeating-conic-gradient(rgb(43 42 51 / 0.25) 0 25%, transparent 0 50%);
		background-size: 4px 4px;
	}

	.close {
		width: 1.75rem;
		height: 1.75rem;
		padding: 0;
		font: inherit;
		font-size: 1.25rem;
		line-height: 1;
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		cursor: pointer;
	}

	/* Laptop: centered modal window. */
	@media (min-width: 768px) {
		dialog {
			width: min(34rem, calc(100% - 2rem));
			/* A fixed dialog with auto height stretches to the viewport; size to content instead. */
			height: fit-content;
			max-height: min(52rem, calc(100dvh - 4rem));
			margin: auto;
			padding: 0 6px 6px 0; /* room for the hard shadow */
			background: transparent;
			overflow: visible;
		}

		dialog[open] {
			display: flex;
		}

		dialog > :global(.window.fill) {
			flex: 1;
			height: auto;
			max-height: calc(min(52rem, 100dvh - 4rem) - 6px);
		}
	}
</style>
