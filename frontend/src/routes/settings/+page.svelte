<script lang="ts">
	import { goto } from '$app/navigation';
	import CategoryManager from '$lib/components/CategoryManager.svelte';
	import ExerciseManager from '$lib/components/ExerciseManager.svelte';
	import { session } from '$lib/session.svelte';
	import Button from '$lib/ui/Button.svelte';
	import Window from '$lib/ui/Window.svelte';

	async function logout() {
		await session.logout();
		await goto('/login');
	}
</script>

<svelte:head><title>Settings · Life Planner</title></svelte:head>

<div class="settings">
	<Window title="Account" accent="paper">
		<dl>
			<dt>Logged in as</dt>
			<dd>{session.user?.username}</dd>
		</dl>
		<p class="hint">
			To change your password for now, run
			<code>docker compose exec app python -m app.cli set-password {session.user?.username}</code>
			on the Pi.
		</p>
		<Button variant="danger" onclick={logout}>Log out</Button>
	</Window>

	<Window title="Expense categories" accent="peach">
		<CategoryManager />
	</Window>

	<Window title="Exercises" accent="mint">
		<ExerciseManager />
	</Window>
</div>

<style>
	.settings {
		max-width: 40rem;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	dl {
		margin: 0 0 1rem;
	}

	dt {
		font-family: var(--font-pixel);
		color: var(--color-muted);
	}

	dd {
		margin: 0;
		font-size: 1.1rem;
	}

	.hint {
		font-size: 0.85rem;
		color: var(--color-muted);
		overflow-wrap: anywhere;
	}
</style>
