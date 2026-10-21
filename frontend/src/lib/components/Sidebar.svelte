<script lang="ts">
	import { page } from '$app/state';
	import { accentVar, isActive, modules } from '$lib/modules';
	import Pixel from '$lib/ui/Pixel.svelte';
	import { icons } from '$lib/ui/icons';
</script>

<nav class="sidebar" aria-label="Modules">
	<ul>
		{#each modules as module (module.href)}
			<li>
				<a
					href={module.href}
					class:active={isActive(module, page.url.pathname)}
					aria-current={isActive(module, page.url.pathname) ? 'page' : undefined}
					style:--accent={accentVar(module.accent)}
				>
					<Pixel art={icons[module.icon]} size={20} />
					<span>{module.label}</span>
				</a>
			</li>
		{/each}
	</ul>
</nav>

<style>
	.sidebar {
		display: none;
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	a {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 0.75rem;
		color: inherit;
		text-decoration: none;
		font-family: var(--font-pixel);
		border: 2px solid transparent;
	}

	a:hover {
		border-color: var(--color-ink);
		background: var(--color-surface);
	}

	a.active {
		background: var(--accent);
		border-color: var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
	}

	@media (min-width: 1024px) {
		.sidebar {
			display: block;
			position: sticky;
			top: 4.25rem;
			align-self: start;
			padding: 1.5rem 0 1.5rem 1.5rem;
		}
	}
</style>
