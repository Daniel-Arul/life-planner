<script lang="ts">
	import type { Snippet } from 'svelte';
	import Dock from './Dock.svelte';
	import EditorHost from './EditorHost.svelte';
	import MenuBar from './MenuBar.svelte';
	import Sidebar from './Sidebar.svelte';

	let { children }: { children: Snippet } = $props();
</script>

<div class="shell">
	<MenuBar />
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
