<script lang="ts">
	import { goto } from '$app/navigation';
	import { editor } from '$lib/editor.svelte';
	import type { Accent } from '$lib/modules';
	import Pixel from '$lib/ui/Pixel.svelte';
	import Sheet from '$lib/ui/Sheet.svelte';
	import { icons } from '$lib/ui/icons';
	import { formatDay, todayStr } from '$lib/dates';
	import EventForm from './EventForm.svelte';
	import TodoForm from './TodoForm.svelte';

	const target = $derived(editor.target);

	const heading = $derived.by((): { title: string; accent: Accent } => {
		if (!target) return { title: '', accent: 'lavender' };
		if (target.kind === 'event') return { title: target.event ? 'Edit event' : 'New event', accent: 'lavender' };
		if (target.kind === 'todo') return { title: target.todo ? 'Edit to-do' : 'New to-do', accent: 'butter' };
		return { title: `Add to ${formatDay(target.date)}`, accent: 'lavender' };
	});

	function saved() {
		editor.close();
		editor.changed();
	}

	function addEvent(date: string, time?: string) {
		editor.open({ kind: 'event', draft: { startDate: date, startTime: time } });
	}

	// Laptop shortcuts: n = new item, g then h/c/t = go to home/calendar/to-dos.
	let pendingG = 0;
	function onkeydown(e: KeyboardEvent) {
		if (e.metaKey || e.ctrlKey || e.altKey || editor.target) return;
		const el = e.target as HTMLElement;
		if (el.closest('input, textarea, select, [contenteditable="true"]')) return;

		if (Date.now() - pendingG < 1000) {
			const dest = { h: '/', c: '/calendar', t: '/todos' }[e.key];
			pendingG = 0;
			if (dest) {
				e.preventDefault();
				goto(dest);
			}
		} else if (e.key === 'g') {
			pendingG = Date.now();
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
			</div>
			<p class="soon">Workouts, expenses and ideas join this menu in later milestones.</p>
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
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
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

	.soon {
		margin: 1rem 0 0;
		font-size: 0.85rem;
		color: var(--color-muted);
		text-align: center;
	}

	@media (min-width: 1024px) {
		.fab {
			display: none;
		}
	}
</style>
