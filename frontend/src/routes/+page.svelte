<script lang="ts">
	import { session } from '$lib/session.svelte';
	import EmptyState from '$lib/ui/EmptyState.svelte';
	import Window from '$lib/ui/Window.svelte';

	const today = new Date().toLocaleDateString([], {
		weekday: 'long',
		month: 'long',
		day: 'numeric'
	});
</script>

<svelte:head><title>Home · Life Planner</title></svelte:head>

<div class="dashboard">
	<header class="greeting">
		<h1>Hello, {session.user?.username}</h1>
		<p>{today}</p>
	</header>

	<div class="grid">
		<Window title="Today" accent="lavender">
			<EmptyState message="Nothing planned" hint="Events arrive in milestone 2." />
		</Window>
		<Window title="To-dos" accent="butter">
			<EmptyState message="All clear" hint="To-dos arrive in milestone 2." />
		</Window>
		<Window title="This week's workouts" accent="mint">
			<EmptyState message="No workouts logged" hint="Workouts arrive in milestone 4." />
		</Window>
		<Window title="Month-to-date spending" accent="peach">
			<EmptyState message="No expenses yet" hint="Expenses arrive in milestone 3." />
		</Window>
		<Window title="Latest ideas" accent="sky">
			<EmptyState message="No ideas jotted" hint="Ideas arrive in milestone 5." />
		</Window>
	</div>
</div>

<style>
	.greeting h1 {
		margin: 0;
		font-size: 1.75rem;
	}

	.greeting p {
		margin: 0.25rem 0 0;
		color: var(--color-muted);
	}

	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.grid {
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		gap: 1rem;
	}

	@media (min-width: 768px) {
		.grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
			gap: 1.5rem;
		}
	}

	@media (min-width: 1280px) {
		.grid {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}
</style>
