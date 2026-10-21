<script lang="ts">
	import type { Snippet } from 'svelte';
	import { accentVar, type Accent } from '$lib/modules';

	let {
		title,
		accent = 'lavender',
		class: className = '',
		fill = false,
		actions,
		children
	}: {
		title: string;
		accent?: Accent;
		class?: string;
		/** Stretch to the parent's height and scroll the body instead of the page. */
		fill?: boolean;
		/** Optional controls shown at the right of the title bar. */
		actions?: Snippet;
		children: Snippet;
	} = $props();
</script>

<section class="window {className}" class:fill style:--accent={accentVar(accent)}>
	<header class="titlebar">
		<span class="box" aria-hidden="true"></span>
		<h2>{title}</h2>
		{#if actions}
			<div class="actions">{@render actions()}</div>
		{:else}
			<span class="box" aria-hidden="true"></span>
		{/if}
	</header>
	<div class="body">
		{@render children()}
	</div>
</section>

<style>
	.window {
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
		min-width: 0;
	}

	.titlebar {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.25rem 0.5rem;
		border-bottom: 2px solid var(--color-ink);
		background-color: var(--accent);
	}

	h2 {
		margin: 0;
		flex: 1;
		font-size: 1rem;
		line-height: 1.5;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.box {
		display: none;
		width: 0.75rem;
		height: 0.75rem;
		border: 2px solid var(--color-ink);
		background: var(--color-surface);
		flex-shrink: 0;
	}

	.actions {
		display: flex;
		gap: 0.25rem;
	}

	.body {
		padding: 1rem;
	}

	.fill {
		display: flex;
		flex-direction: column;
		height: 100%;
		box-sizing: border-box;
	}

	.fill .body {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow-y: auto;
		overscroll-behavior: contain;
	}

	/* Full retro chrome when there's room: hard shadow, pinstripes, close boxes. */
	@media (min-width: 768px) {
		.window {
			box-shadow: var(--shadow-hard);
		}

		.titlebar {
			background-image: repeating-linear-gradient(
				to bottom,
				transparent 0 2px,
				color-mix(in srgb, var(--color-ink) 18%, transparent) 2px 3px
			);
		}

		h2 {
			flex: 0 1 auto;
			margin-inline: auto;
			padding-inline: 0.5rem;
			background: var(--accent);
		}

		.box {
			display: block;
		}
	}
</style>
