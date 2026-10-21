<script lang="ts">
	import { page } from '$app/state';
	import { accentVar, isActive, modules } from '$lib/modules';
	import Pixel from '$lib/ui/Pixel.svelte';
	import { icons } from '$lib/ui/icons';

	const dockModules = modules.filter((m) => m.inDock);
</script>

<nav class="dock" aria-label="Modules">
	{#each dockModules as module (module.href)}
		<a
			href={module.href}
			class:active={isActive(module, page.url.pathname)}
			aria-current={isActive(module, page.url.pathname) ? 'page' : undefined}
			style:--accent={accentVar(module.accent)}
		>
			<Pixel art={icons[module.icon]} size={22} />
			<span>{module.label}</span>
		</a>
	{/each}
</nav>

<style>
	.dock {
		position: fixed;
		inset: auto 0 0 0;
		z-index: 20;
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		height: calc(var(--dock-height) + env(safe-area-inset-bottom));
		padding: 0 env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
		background: var(--color-surface);
		border-top: 2px solid var(--color-ink);
	}

	a {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.2rem;
		min-width: 0;
		color: inherit;
		text-decoration: none;
		font-family: var(--font-pixel);
		font-size: 0.65rem;
		border-inline: 1px solid transparent;
	}

	a.active {
		background: var(--accent);
		border-inline-color: var(--color-ink);
	}

	span {
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	@media (min-width: 1024px) {
		.dock {
			display: none;
		}
	}
</style>
