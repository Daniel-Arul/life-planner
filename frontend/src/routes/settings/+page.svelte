<script lang="ts">
	import { goto } from '$app/navigation';
	import CategoryManager from '$lib/components/CategoryManager.svelte';
	import ExerciseManager from '$lib/components/ExerciseManager.svelte';
	import { session } from '$lib/session.svelte';
	import Button from '$lib/ui/Button.svelte';
	import Window from '$lib/ui/Window.svelte';

	const CSV_EXPORTS = [
		{ dataset: 'todos', label: 'To-dos' },
		{ dataset: 'events', label: 'Events' },
		{ dataset: 'expenses', label: 'Expenses' },
		{ dataset: 'workouts', label: 'Workouts' },
		{ dataset: 'ideas', label: 'Ideas' }
	];

	const SHORTCUTS = [
		{ keys: ['n'], action: 'Add something' },
		{ keys: ['/'], action: 'Search (on Ideas)' },
		{ keys: ['g', 'h'], action: 'Go home' },
		{ keys: ['g', 'c'], action: 'Calendar' },
		{ keys: ['g', 't'], action: 'To-dos' },
		{ keys: ['g', 'e'], action: 'Expenses' },
		{ keys: ['g', 'w'], action: 'Workouts' },
		{ keys: ['g', 'i'], action: 'Ideas' },
		{ keys: ['Esc'], action: 'Close a form' },
		{ keys: ['Ctrl/⌘', 'Enter'], action: 'Save an idea' }
	];

	// Running from the home screen (installed) vs in a browser tab.
	const installed =
		typeof window !== 'undefined' && window.matchMedia('(display-mode: standalone)').matches;

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

	<Window title="Your data" accent="paper">
		<p class="hint">
			Everything you've logged, as files you keep. The JSON file has all of it (handy as an extra
			backup); the CSV files open in any spreadsheet.
		</p>
		<div class="downloads">
			<a class="download primary" href="/api/export.json" download>⤓ Everything (JSON)</a>
			{#each CSV_EXPORTS as item (item.dataset)}
				<a class="download" href="/api/export/{item.dataset}.csv" download>⤓ {item.label} (CSV)</a>
			{/each}
		</div>
	</Window>

	<Window title="Expense categories" accent="peach">
		<CategoryManager />
	</Window>

	<Window title="Exercises" accent="mint">
		<ExerciseManager />
	</Window>

	<Window title="On your phone" accent="sky">
		{#if installed}
			<p>You're using the installed app.</p>
		{:else}
			<p class="hint">Add Life Planner to your home screen so it opens like an app:</p>
			<ul class="steps">
				<li><strong>iPhone (Safari):</strong> Share button → <em>Add to Home Screen</em>.</li>
				<li><strong>Android (Chrome):</strong> ⋮ menu → <em>Install app</em>.</li>
			</ul>
			<p class="hint">Keep the Tailscale app connected on your phone so it can reach the Pi.</p>
		{/if}
		<p class="hint">Long-press the installed icon for shortcuts: add a to-do, expense, workout or idea.</p>
	</Window>

	<div class="keys-window">
		<Window title="Keyboard shortcuts" accent="paper">
			<table class="keys">
				<tbody>
					{#each SHORTCUTS as s (s.action)}
						<tr>
							<td>
								{#each s.keys as key, i (key)}{#if i > 0}<span class="then">then</span>{/if}<kbd>{key}</kbd>{/each}
							</td>
							<td>{s.action}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</Window>
	</div>
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

	p {
		margin: 0 0 0.75rem;
	}

	.hint {
		font-size: 0.85rem;
		color: var(--color-muted);
		overflow-wrap: anywhere;
	}

	.downloads {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.download {
		display: inline-flex;
		align-items: center;
		min-height: 40px;
		padding: 0 0.75rem;
		font-family: var(--font-pixel);
		font-size: 0.9rem;
		color: var(--color-ink);
		text-decoration: none;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
	}

	.download.primary {
		background: var(--color-lavender);
	}

	.download:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}

	.steps {
		margin: 0 0 0.75rem;
		padding-left: 1.2rem;
		list-style: square;
	}

	.steps li {
		margin-bottom: 0.3rem;
	}

	/* Shortcuts only matter with a keyboard and mouse. */
	@media (hover: none) {
		.keys-window {
			display: none;
		}
	}

	.keys {
		border-collapse: collapse;
		font-size: 0.9rem;
	}

	.keys td {
		padding: 0.25rem 1rem 0.25rem 0;
		vertical-align: middle;
	}

	kbd {
		display: inline-block;
		min-width: 1.5rem;
		padding: 0 0.35rem;
		font-family: var(--font-mono);
		font-size: 0.85rem;
		text-align: center;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		box-shadow: 0 2px 0 var(--color-ink);
	}

	.then {
		margin: 0 0.3rem;
		font-size: 0.75rem;
		color: var(--color-muted);
	}
</style>
