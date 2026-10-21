<script lang="ts">
	import { goto } from '$app/navigation';
	import { editor } from '$lib/editor.svelte';
	import type { Accent } from '$lib/modules';
	import Pixel from '$lib/ui/Pixel.svelte';
	import Sheet from '$lib/ui/Sheet.svelte';
	import { icons } from '$lib/ui/icons';
	import { formatDay, todayStr } from '$lib/dates';
	import EventForm from './EventForm.svelte';
	import ExpenseForm from './ExpenseForm.svelte';
	import IdeaForm from './IdeaForm.svelte';
	import TodoForm from './TodoForm.svelte';
	import WorkoutForm from './WorkoutForm.svelte';

	const target = $derived(editor.target);

	const heading = $derived.by((): { title: string; accent: Accent } => {
		if (!target) return { title: '', accent: 'lavender' };
		if (target.kind === 'event') return { title: target.event ? 'Edit event' : 'New event', accent: 'lavender' };
		if (target.kind === 'todo') return { title: target.todo ? 'Edit to-do' : 'New to-do', accent: 'butter' };
		if (target.kind === 'expense')
			return { title: target.expense ? 'Edit expense' : 'New expense', accent: 'peach' };
		if (target.kind === 'workout')
			return { title: target.workout ? 'Edit workout' : 'Log workout', accent: 'mint' };
		if (target.kind === 'idea') return { title: target.idea ? 'Edit idea' : 'New idea', accent: 'sky' };
		return { title: `Add to ${formatDay(target.date)}`, accent: 'lavender' };
	});

	function saved() {
		editor.close();
		editor.changed();
	}

	function addEvent(date: string, time?: string) {
		editor.open({ kind: 'event', draft: { startDate: date, startTime: time } });
	}

	// Laptop shortcuts: n = new item, / = search, g then h/c/t/e/w/i = go to
	// home/calendar/to-dos/expenses/workouts/ideas.
	let pendingG = 0;
	function onkeydown(e: KeyboardEvent) {
		if (e.metaKey || e.ctrlKey || e.altKey || editor.target) return;
		const el = e.target as HTMLElement;
		if (el.closest('input, textarea, select, [contenteditable="true"]')) return;

		if (Date.now() - pendingG < 1000) {
			const dest = { h: '/', c: '/calendar', t: '/todos', e: '/expenses', w: '/workouts', i: '/ideas' }[e.key];
			pendingG = 0;
			if (dest) {
				e.preventDefault();
				goto(dest);
			}
		} else if (e.key === 'g') {
			pendingG = Date.now();
		} else if (e.key === '/') {
			// Focus the page's search box, if it has one.
			const search = document.querySelector<HTMLInputElement>('[data-search]');
			if (search) {
				e.preventDefault();
				search.focus();
			}
		} else if (e.key === 'n') {
			e.preventDefault();
			editor.open({ kind: 'chooser', date: todayStr() });
		}
	}
</script>

<svelte:window {onkeydown} />

<!-- Phone quick-add button, floating above the dock. -->
<button
	type="button"
	class="fab"
	aria-label="Add something"
	onclick={() => editor.open({ kind: 'chooser', date: todayStr() })}
>
	<Pixel art={icons.plus} size={26} />
</button>

<Sheet open={target !== null} title={heading.title} accent={heading.accent} onclose={() => editor.close()}>
	{#key target}
		{#if target?.kind === 'event'}
			<EventForm event={target.event} draft={target.draft} onsaved={saved} oncancel={() => editor.close()} />
		{:else if target?.kind === 'todo'}
			<TodoForm todo={target.todo} dueDate={target.dueDate} onsaved={saved} oncancel={() => editor.close()} />
		{:else if target?.kind === 'expense'}
			<ExpenseForm expense={target.expense} date={target.date} onsaved={saved} oncancel={() => editor.close()} />
		{:else if target?.kind === 'workout'}
			<WorkoutForm workout={target.workout} date={target.date} onsaved={saved} oncancel={() => editor.close()} />
		{:else if target?.kind === 'idea'}
			<IdeaForm idea={target.idea} title={target.title} onsaved={saved} oncancel={() => editor.close()} />
		{:else if target?.kind === 'chooser'}
			<div class="chooser">
				<button
					type="button"
					style:--accent="var(--color-lavender)"
					onclick={() => addEvent(target.date, target.time)}
				>
					<Pixel art={icons.calendar} size={32} />
					<span>Event</span>
				</button>
				<button
					type="button"
					style:--accent="var(--color-butter)"
					onclick={() => editor.open({ kind: 'todo', dueDate: target.date })}
				>
					<Pixel art={icons.todo} size={32} />
					<span>To-do</span>
				</button>
				<button
					type="button"
					style:--accent="var(--color-peach)"
					onclick={() => editor.open({ kind: 'expense', date: target.date })}
				>
					<Pixel art={icons.expense} size={32} />
					<span>Expense</span>
				</button>
				<button
					type="button"
					style:--accent="var(--color-mint)"
					onclick={() => editor.open({ kind: 'workout', date: target.date })}
				>
					<Pixel art={icons.workout} size={32} />
					<span>Workout</span>
				</button>
				<button type="button" style:--accent="var(--color-sky)" onclick={() => editor.open({ kind: 'idea' })}>
					<Pixel art={icons.idea} size={32} />
					<span>Idea</span>
				</button>
			</div>
		{/if}
	{/key}
</Sheet>

<style>
	.fab {
		position: fixed;
		right: calc(1rem + env(safe-area-inset-right));
		bottom: calc(var(--dock-height) + 1rem + env(safe-area-inset-bottom));
		z-index: 25;
		display: grid;
		place-items: center;
		width: 56px;
		height: 56px;
		color: var(--color-ink);
		background: var(--color-lavender);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard);
		cursor: pointer;
	}

	.fab:active {
		transform: translate(4px, 4px);
		box-shadow: none;
	}

	.chooser {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	@media (min-width: 768px) {
		.chooser {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}

	.chooser button {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1.25rem 0.5rem;
		font-family: var(--font-pixel);
		font-size: 1.1rem;
		color: var(--color-ink);
		background: var(--accent);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
		cursor: pointer;
	}

	.chooser button:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}

	@media (min-width: 1024px) {
		.fab {
			display: none;
		}
	}
</style>
