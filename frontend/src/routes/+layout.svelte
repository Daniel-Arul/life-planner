<script lang="ts">
	import '@fontsource/ibm-plex-mono/400.css';
	import '@fontsource/ibm-plex-mono/600.css';
	import '../app.css';

	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import AppShell from '$lib/components/AppShell.svelte';
	import { connection } from '$lib/connection.svelte';
	import { session } from '$lib/session.svelte';
	import Button from '$lib/ui/Button.svelte';
	import Window from '$lib/ui/Window.svelte';
	import ProgressBar from '$lib/ui/ProgressBar.svelte';
	import { onMount } from 'svelte';

	let { children } = $props();

	const onLoginPage = $derived(page.url.pathname === '/login');

	onMount(() => {
		session.load();
	});

	// Couldn't check the session because the Pi is unreachable: don't bounce to login.
	const offline = $derived(session.loaded && !session.user && !connection.reachable);

	async function retry() {
		session.loaded = false;
		await session.load();
	}

	$effect(() => {
		if (!session.loaded || offline) return;
		if (!session.user && !onLoginPage) goto('/login');
		else if (session.user && onLoginPage) goto('/');
	});
</script>

{#if !session.loaded}
	<div class="boot"><ProgressBar label="Booting" /></div>
{:else if offline}
	<div class="boot">
		<div class="offline">
			<Window title="No connection" accent="rose">
				<p>Can't reach your planner.</p>
				<p class="hint">
					Check that Tailscale is connected on this device, and that the Pi is on.
				</p>
				<Button variant="primary" onclick={retry}>Try again</Button>
			</Window>
		</div>
	</div>
{:else if onLoginPage}
	{@render children()}
{:else if session.user}
	<AppShell>{@render children()}</AppShell>
{/if}

<style>
	.boot {
		display: grid;
		place-items: center;
		min-height: 100dvh;
		padding: 1rem;
		box-sizing: border-box;
	}

	.offline {
		width: 100%;
		max-width: 22rem;
	}

	.offline p {
		margin: 0 0 0.75rem;
	}

	.hint {
		font-size: 0.85rem;
		color: var(--color-muted);
	}
</style>
