<script lang="ts">
	import type { Snippet } from 'svelte';
	import Dock from './Dock.svelte';
	import EditorHost from './EditorHost.svelte';
	import MenuBar from './MenuBar.svelte';
	import Sidebar from './Sidebar.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { appConfig } from '$lib/config.svelte';
	import { connection } from '$lib/connection.svelte';
	import { todayStr } from '$lib/dates';
	import { editor, type EditorTarget } from '$lib/editor.svelte';
	import { onMount } from 'svelte';

	let { children }: { children: Snippet } = $props();

	onMount(() => {
		appConfig.load();
	});

	// Home-screen shortcuts (manifest) link to e.g. /todos?add=todo.
	const ADD_TARGETS: Record<string, () => EditorTarget> = {
		todo: () => ({ kind: 'todo' }),
		event: () => ({ kind: 'event', draft: { startDate: todayStr() } }),
		expense: () => ({ kind: 'expense' }),
		workout: () => ({ kind: 'workout', date: todayStr() }),
		idea: () => ({ kind: 'idea' })
	};

	$effect(() => {
		const add = page.url.searchParams.get('add');
		if (!add || !(add in ADD_TARGETS)) return;
		editor.open(ADD_TARGETS[add]());
		const url = new URL(page.url);
		url.searchParams.delete('add');
		goto(url.pathname + url.search, { replaceState: true, noScroll: true, keepFocus: true });
	});

	function retry() {
		connection.reachable = true;
		editor.changed(); // every open page refetches
	}
</script>

<div class="shell">
	<MenuBar />
	{#if !connection.reachable}
		<div class="offline-bar" role="alert">
			<span><strong>Offline.</strong> Can't reach your planner. Is Tailscale connected?</span>
			<button type="button" onclick={retry}>Retry</button>
		</div>
	{/if}
	<div class="frame">
		<Sidebar />
		<main>{@render children()}</main>
	</div>
	<Dock />
	<EditorHost />
</div>

<style>
	.shell {
		--dock-height: 3.75rem;
		min-height: 100dvh;
		display: flex;
		flex-direction: column;
	}

	.frame {
		flex: 1;
	}

	.offline-bar {
		position: sticky;
		top: calc(2.75rem + env(safe-area-inset-top));
		z-index: 19;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		padding: 0.4rem 0.75rem;
		font-size: 0.9rem;
		background: var(--color-rose);
		border-bottom: 2px solid var(--color-ink);
	}

	.offline-bar button {
		min-height: 36px;
		padding: 0 0.75rem;
		font-family: var(--font-pixel);
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		cursor: pointer;
	}

	main {
		width: 100%;
		max-width: 80rem;
		margin-inline: auto;
		padding: 1rem;
		/* Keep content clear of the fixed dock and the iPhone home bar. */
		padding-bottom: calc(var(--dock-height) + 1.5rem + env(safe-area-inset-bottom));
		box-sizing: border-box;
	}

	@media (min-width: 1024px) {
		.frame {
			display: grid;
			grid-template-columns: 15rem minmax(0, 1fr);
		}

		main {
			padding: 1.5rem;
		}
	}
</style>
