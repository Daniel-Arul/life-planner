<script lang="ts">
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import { session } from '$lib/session.svelte';
	import Button from '$lib/ui/Button.svelte';
	import Pixel from '$lib/ui/Pixel.svelte';
	import TextField from '$lib/ui/TextField.svelte';
	import Window from '$lib/ui/Window.svelte';
	import { floppy } from '$lib/ui/icons';

	let username = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let busy = $state(false);

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		busy = true;
		error = null;
		try {
			await session.login(username, password);
			await goto('/');
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not reach the planner. Is it running?';
		} finally {
			busy = false;
		}
	}
</script>

<svelte:head><title>Log in · Life Planner</title></svelte:head>

<div class="screen">
	<div class="stack">
		<div class="logo">
			<Pixel art={floppy} size={48} />
			<h1>Life Planner</h1>
		</div>

		<Window title="Log in" accent="lavender">
			<form onsubmit={submit}>
				<TextField
					label="Username"
					bind:value={username}
					autocomplete="username"
					autocapitalize="none"
					spellcheck={false}
					required
				/>
				<TextField
					label="Password"
					type="password"
					bind:value={password}
					autocomplete="current-password"
					required
				/>
				{#if error}
					<p class="error" role="alert">{error}</p>
				{/if}
				<Button type="submit" variant="primary" disabled={busy}>
					{busy ? 'Logging in…' : 'Log in'}
				</Button>
			</form>
		</Window>

		<p class="version">System 0.1 · private over Tailscale</p>
	</div>
</div>

<style>
	.screen {
		display: grid;
		place-items: center;
		min-height: 100dvh;
		padding: 1rem;
		box-sizing: border-box;
	}

	.stack {
		width: 100%;
		max-width: 22rem;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.logo {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	h1 {
		margin: 0;
		font-size: 1.75rem;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.error {
		margin: 0;
		padding: 0.5rem 0.75rem;
		background: var(--color-rose);
		border: 2px solid var(--color-ink);
	}

	.version {
		margin: 0;
		text-align: center;
		font-size: 0.8rem;
		color: var(--color-muted);
	}
</style>
