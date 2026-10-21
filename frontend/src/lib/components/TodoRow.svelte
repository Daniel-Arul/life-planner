<script lang="ts">
	import { daysFromToday, formatDay } from '$lib/dates';
	import type { Todo } from '$lib/types';
	import Pixel from '$lib/ui/Pixel.svelte';

	let {
		todo,
		ontoggle,
		onopen,
		draggable = false,
		dragging = false,
		ondragstart
	}: {
		todo: Todo;
		ontoggle: (todo: Todo) => void;
		onopen: (todo: Todo) => void;
		draggable?: boolean;
		dragging?: boolean;
		ondragstart?: (e: PointerEvent) => void;
	} = $props();

	const HANDLE = ['##.##', '.....', '##.##', '.....', '##.##', '.....', '##.##'];

	const done = $derived(todo.status === 'done');
	const dueIn = $derived(todo.due_date ? daysFromToday(todo.due_date) : null);
	const dueAccent = $derived(
		done || dueIn === null ? undefined : dueIn < 0 ? 'var(--color-rose)' : dueIn === 0 ? 'var(--color-butter)' : undefined
	);
</script>

<li class="row" class:done class:dragging data-todo-id={todo.id}>
	{#if draggable}
		<button
			type="button"
			class="handle"
			aria-label="Drag to reorder {todo.title}"
			onpointerdown={ondragstart}
		>
			<Pixel art={HANDLE} size={10} />
		</button>
	{/if}

	<input
		type="checkbox"
		class="retro-check check"
		checked={done}
		aria-label="Mark {todo.title} {done ? 'not done' : 'done'}"
		onchange={() => ontoggle(todo)}
	/>

	<button type="button" class="main" onclick={() => onopen(todo)}>
		<span class="title">{todo.title}</span>
		<span class="meta">
			{#if todo.priority > 0}
				<span class="priority" aria-label="priority {todo.priority} of 3">{'!'.repeat(todo.priority)}</span>
			{/if}
			{#if todo.due_date}
				<span class="badge" style:--badge-accent={dueAccent}>
					{dueIn !== null && dueIn < 0 && !done ? 'Overdue · ' : ''}{formatDay(todo.due_date)}
				</span>
			{/if}
			{#if todo.tag}<span class="badge tag">#{todo.tag}</span>{/if}
		</span>
	</button>
</li>

<style>
	.row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.25rem 0.5rem;
		background: var(--color-surface);
		border-bottom: 2px dotted var(--color-grid);
	}

	.row:last-child {
		border-bottom: 0;
	}

	.row.dragging {
		position: relative;
		z-index: 1;
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
		background: color-mix(in srgb, var(--color-butter) 30%, var(--color-surface));
	}

	.handle {
		display: grid;
		place-items: center;
		width: 28px;
		align-self: stretch;
		padding: 0;
		color: var(--color-muted);
		background: none;
		border: 0;
		cursor: grab;
		/* Let the pointer drag the row instead of scrolling the page. */
		touch-action: none;
	}

	.check {
		width: 1.5rem;
		height: 1.5rem;
		margin: 0.6rem 0.25rem;
	}

	.main {
		flex: 1;
		min-width: 0;
		min-height: 44px;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.25rem 0.75rem;
		padding: 0.4rem 0;
		font: inherit;
		color: inherit;
		text-align: left;
		background: none;
		border: 0;
		cursor: pointer;
	}

	.title {
		flex: 1 1 12rem;
		min-width: 0;
		overflow-wrap: anywhere;
	}

	.done .title {
		color: var(--color-muted);
		text-decoration: line-through;
		text-decoration-thickness: 2px;
	}

	.meta {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.4rem;
	}

	.priority {
		font-family: var(--font-pixel);
		color: var(--color-alert);
		letter-spacing: 0.1em;
	}

	.tag {
		--badge-accent: color-mix(in srgb, var(--color-sky) 45%, var(--color-surface));
	}

	@media (hover: hover) {
		.main:hover .title {
			text-decoration: underline;
			text-decoration-style: dotted;
		}
	}
</style>
