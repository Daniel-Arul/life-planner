<script lang="ts">
	import '@fontsource/ibm-plex-mono/400.css';
	import '@fontsource/ibm-plex-mono/600.css';
	import '../app.css';

	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import AppShell from '$lib/components/AppShell.svelte';
	import { session } from '$lib/session.svelte';
	import ProgressBar from '$lib/ui/ProgressBar.svelte';
	import { onMount } from 'svelte';

	let { children } = $props();

	const onLoginPage = $derived(page.url.pathname === '/login');

	onMount(() => {
		session.load();
	});

	$effect(() => {
		if (!session.loaded) return;
		if (!session.user && !onLoginPage) goto('/login');
		else if (session.user && onLoginPage) goto('/');
	});
</script>

{#if !session.loaded}
	<div class="boot"><ProgressBar label="Booting" /></div>
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
	}
</style>
