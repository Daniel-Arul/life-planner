<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { currentModule } from '$lib/modules';
	import { session } from '$lib/session.svelte';
	import Pixel from '$lib/ui/Pixel.svelte';
	import { floppy, icons } from '$lib/ui/icons';

	let now = $state(new Date());

	$effect(() => {
		const timer = setInterval(() => (now = new Date()), 15_000);
		return () => clearInterval(timer);
	});

	const clock = $derived(
		now.toLocaleString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' })
	);
	const current = $derived(currentModule(page.url.pathname));

	async function logout() {
		await session.logout();
		await goto('/login');
	}
</script>

<header class="menubar">
	<a href="/" class="brand">
		<Pixel art={floppy} size={18} />
		<span>Life Planner</span>
	</a>
	{#if current}
		<span class="current">{current.label}</span>
	{/if}

	<div class="right">
		<time class="clock tabular">{clock}</time>
		<a href="/settings" class="icon-btn settings" aria-label="Settings">
			<Pixel art={icons.settings} size={20} />
		</a>
		<button type="button" class="icon-btn logout" onclick={logout}>
			<Pixel art={icons.logout} size={18} />
			<span>Log out</span>
		</button>
	</div>
</header>

<style>
	.menubar {
		position: sticky;
		top: 0;
		z-index: 20;
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0 0.75rem;
		padding-top: env(safe-area-inset-top);
		min-height: calc(2.75rem + env(safe-area-inset-top));
		background: var(--color-surface);
		border-bottom: 2px solid var(--color-ink);
		font-family: var(--font-pixel);
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: inherit;
		text-decoration: none;
		font-size: 1.05rem;
	}

	.current {
		padding: 0 0.5rem;
		border-left: 2px solid var(--color-ink);
		color: var(--color-muted);
	}

	.right {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.icon-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		min-width: 44px;
		min-height: 44px;
		padding: 0 0.5rem;
		font: inherit;
		color: inherit;
		background: none;
		border: 0;
		cursor: pointer;
	}

	.clock,
	.logout {
		display: none;
	}

	@media (hover: hover) {
		.icon-btn:hover {
			background: var(--color-ink);
			color: var(--color-surface);
		}
	}

	/* Laptop: clock + log out in the bar; settings moves to the sidebar. */
	@media (min-width: 1024px) {
		.clock {
			display: inline;
			padding-inline: 0.75rem;
		}

		.logout {
			display: inline-flex;
		}

		.settings {
			display: none;
		}
	}
</style>
