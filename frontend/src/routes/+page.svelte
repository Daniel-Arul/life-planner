<script lang="ts">
	import TodoRow from '$lib/components/TodoRow.svelte';
	import { expenses as expensesApi, fetchCalendar, todos as todosApi } from '$lib/data';
	import { addDays, daysFromToday, formatTime, parseLocal, toMonthStr, todayStr } from '$lib/dates';
	import { editor } from '$lib/editor.svelte';
	import { session } from '$lib/session.svelte';
	import { formatMoney } from '$lib/money';
	import type { CalendarItem, ExpenseStats, Todo } from '$lib/types';
	import BudgetMeter from '$lib/ui/BudgetMeter.svelte';
	import Button from '$lib/ui/Button.svelte';
	import EmptyState from '$lib/ui/EmptyState.svelte';
	import Window from '$lib/ui/Window.svelte';

	const TODO_LIMIT = 6;

	const today = new Date().toLocaleDateString([], {
		weekday: 'long',
		month: 'long',
		day: 'numeric'
	});

	let agenda = $state<CalendarItem[]>([]);
	let openTodos = $state<Todo[]>([]);
	let spending = $state<ExpenseStats | null>(null);
	let loaded = $state(false);

	// Most pressing first: overdue, then due today, then by the list's own order.
	const pressing = $derived(
		[...openTodos]
			.sort((a, b) => urgency(a) - urgency(b))
			.slice(0, TODO_LIMIT)
	);
	const overdueCount = $derived(openTodos.filter((t) => t.due_date && daysFromToday(t.due_date) < 0).length);

	function urgency(todo: Todo) {
		if (!todo.due_date) return 2;
		const days = daysFromToday(todo.due_date);
		return days < 0 ? 0 : days === 0 ? 1 : 2;
	}

	$effect(() => {
		void editor.revision;
		const start = parseLocal(todayStr());
		Promise.all([
			fetchCalendar(start, addDays(start, 1)),
			todosApi.list('open'),
			expensesApi.stats(toMonthStr(start))
		]).then(
			([items, todos, stats]) => {
				spending = stats;
				// To-dos have their own window, so Today shows plans only.
				agenda = items.filter((i) => i.kind === 'event');
				openTodos = todos;
				loaded = true;
			},
			() => (loaded = true)
		);
	});

	async function toggle(todo: Todo) {
		openTodos = openTodos.map((t) => (t.id === todo.id ? { ...t, status: 'done' } : t));
		await todosApi.update(todo.id, { status: todo.status === 'done' ? 'open' : 'done' });
		setTimeout(() => editor.changed(), 400);
	}
</script>

<svelte:head><title>Home · Life Planner</title></svelte:head>

<div class="dashboard">
	<header class="greeting">
		<h1>Hello, {session.user?.username}</h1>
		<p>{today}</p>
	</header>

	<div class="grid">
		<Window title="Today" accent="lavender">
			{#if loaded && agenda.length === 0}
				<EmptyState message="Nothing planned" hint="Enjoy the free day." />
			{:else}
				<ul class="agenda">
					{#each agenda as item (item.id)}
						<li style:--accent="var(--color-{item.color})">
							<button type="button" onclick={() => editor.editEvent(item.source_id)}>
								<span class="when tabular">
									{item.all_day ? 'All day' : formatTime(parseLocal(item.start))}
								</span>
								<span class="what">{item.title}{item.recurring ? ' ↻' : ''}</span>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
			<div class="window-actions">
				<Button onclick={() => editor.open({ kind: 'event', draft: { startDate: todayStr() } })}>
					+ Event
				</Button>
				<a class="more" href="/calendar">Calendar →</a>
			</div>
		</Window>

		<Window title={overdueCount ? `To-dos · ${overdueCount} overdue` : 'To-dos'} accent={overdueCount ? 'rose' : 'butter'}>
			{#if loaded && openTodos.length === 0}
				<EmptyState message="All clear" hint="Nothing left to do." />
			{:else}
				<ul class="todos">
					{#each pressing as todo (todo.id)}
						<TodoRow {todo} ontoggle={toggle} onopen={(t) => editor.open({ kind: 'todo', todo: t })} />
					{/each}
				</ul>
			{/if}
			<div class="window-actions">
				<Button onclick={() => editor.open({ kind: 'todo' })}>+ To-do</Button>
				<a class="more" href="/todos">
					{openTodos.length > TODO_LIMIT ? `All ${openTodos.length} →` : 'To-dos →'}
				</a>
			</div>
		</Window>

		<Window title="This week's workouts" accent="mint">
			<EmptyState message="No workouts logged" hint="Workouts arrive in milestone 4." />
		</Window>
		<Window title="Month-to-date spending" accent="peach">
			{#if spending}
				<p class="spent"><span class="spent-value">{formatMoney(spending.total_cents)}</span> spent so far</p>
				{#if spending.budget_cents}
					<BudgetMeter spent={spending.total_cents} budget={spending.budget_cents} label="Monthly budget" />
				{/if}
				{#if spending.categories.length}
					<ul class="top-cats">
						{#each spending.categories.slice(0, 3) as cat (cat.id ?? 'none')}
							<li>
								<span>{cat.name}</span>
								<span class="tabular">{formatMoney(cat.total_cents)}</span>
							</li>
						{/each}
					</ul>
				{/if}
			{/if}
			<div class="window-actions">
				<Button onclick={() => editor.open({ kind: 'expense' })}>+ Expense</Button>
				<a class="more" href="/expenses">Expenses →</a>
			</div>
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

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.agenda {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.agenda button {
		display: flex;
		gap: 0.75rem;
		width: 100%;
		min-height: 44px;
		align-items: center;
		padding: 0.25rem 0.6rem;
		font: inherit;
		color: inherit;
		text-align: left;
		background: color-mix(in srgb, var(--accent) 45%, var(--color-surface));
		border: 2px solid var(--color-ink);
		border-left-width: 8px;
		border-left-color: var(--accent);
		cursor: pointer;
	}

	.when {
		flex-shrink: 0;
		min-width: 4.5rem;
		font-weight: 600;
	}

	.what {
		min-width: 0;
		overflow-wrap: anywhere;
	}

	.todos {
		border: 2px solid var(--color-ink);
	}

	.spent {
		margin: 0 0 0.75rem;
		color: var(--color-muted);
	}

	.spent-value {
		display: block;
		font-size: 2rem;
		font-weight: 600;
		color: var(--color-ink);
	}

	.top-cats {
		margin-top: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.top-cats li {
		display: flex;
		justify-content: space-between;
		padding-bottom: 0.3rem;
		border-bottom: 2px dotted var(--color-grid);
	}

	.window-actions {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.more {
		font-family: var(--font-pixel);
		color: var(--color-ink);
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
