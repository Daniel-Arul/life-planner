<script lang="ts">
	import { ApiError } from '$lib/api';
	import TodoRow from '$lib/components/TodoRow.svelte';
	import { todos as todosApi } from '$lib/data';
	import { editor } from '$lib/editor.svelte';
	import type { Todo } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import EmptyState from '$lib/ui/EmptyState.svelte';
	import ProgressBar from '$lib/ui/ProgressBar.svelte';
	import Window from '$lib/ui/Window.svelte';

	type StatusFilter = 'open' | 'done' | 'all';
	const STATUS_FILTERS: { value: StatusFilter; label: string }[] = [
		{ value: 'open', label: 'Open' },
		{ value: 'done', label: 'Done' },
		{ value: 'all', label: 'All' }
	];

	let status = $state<StatusFilter>('open');
	let tag = $state<string | null>(null);
	let items = $state<Todo[]>([]);
	let tags = $state<string[]>([]);
	let loaded = $state(false);
	let error = $state<string | null>(null);
	let newTitle = $state('');

	// Manual order only makes sense on the unfiltered list of open to-dos.
	const canReorder = $derived(status === 'open' && tag === null);

	$effect(() => {
		void editor.revision;
		load(status, tag);
	});

	let latest = 0;
	async function load(statusFilter: StatusFilter, tagFilter: string | null) {
		const request = ++latest;
		try {
			const [list, allTags] = await Promise.all([
				todosApi.list(statusFilter, tagFilter ?? undefined),
				todosApi.tags()
			]);
			if (request !== latest) return;
			items = list;
			tags = allTags;
			error = null;
		} catch (err) {
			if (request === latest) error = err instanceof ApiError ? err.message : 'Could not load to-dos.';
		} finally {
			if (request === latest) loaded = true;
		}
	}

	async function quickAdd(e: SubmitEvent) {
		e.preventDefault();
		const title = newTitle.trim();
		if (!title) return;
		newTitle = '';
		try {
			await todosApi.create({ title, notes: '', due_date: null, priority: 0, tag });
			editor.changed();
		} catch (err) {
			newTitle = title;
			error = err instanceof ApiError ? err.message : 'Could not add the to-do.';
		}
	}

	async function toggle(todo: Todo) {
		const next = todo.status === 'done' ? 'open' : 'done';
		// Optimistic: tick it now, then let the reload drop it from the filtered list.
		items = items.map((t) => (t.id === todo.id ? { ...t, status: next } : t));
		try {
			await todosApi.update(todo.id, { status: next });
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not update the to-do.';
		}
		setTimeout(() => editor.changed(), 400);
	}

	// --- Drag to reorder (pointer events, so it works with touch and mouse) ---
	let listEl: HTMLUListElement | undefined = $state();
	let dragId = $state<number | null>(null);

	function startDrag(e: PointerEvent, id: number) {
		if (!canReorder) return;
		e.preventDefault();
		dragId = id;
		window.addEventListener('pointermove', moveDrag);
		window.addEventListener('pointerup', endDrag, { once: true });
		window.addEventListener('pointercancel', endDrag, { once: true });
	}

	function moveDrag(e: PointerEvent) {
		if (dragId === null || !listEl) return;
		const rows = [...listEl.querySelectorAll<HTMLElement>('[data-todo-id]')];
		const from = items.findIndex((t) => t.id === dragId);
		// Insert before the first row whose middle is below the pointer.
		let to = rows.findIndex((row) => {
			const box = row.getBoundingClientRect();
			return e.clientY < box.top + box.height / 2;
		});
		if (to === -1) to = rows.length - 1;
		else if (to > from) to -= 1;
		if (to !== from) {
			const next = [...items];
			const [moved] = next.splice(from, 1);
			next.splice(to, 0, moved);
			items = next;
		}
	}

	async function endDrag() {
		window.removeEventListener('pointermove', moveDrag);
		if (dragId === null) return;
		dragId = null;
		try {
			await todosApi.reorder(items.map((t) => t.id));
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not save the new order.';
			editor.changed();
		}
	}
</script>

<svelte:head><title>To-dos · Life Planner</title></svelte:head>

<div class="page">
	<Window title="To-dos" accent="butter">
		<form class="quick-add" onsubmit={quickAdd}>
			<label class="sr-only" for="new-todo">New to-do</label>
			<input
				id="new-todo"
				class="retro-input"
				placeholder={tag ? `Add a #${tag} to-do…` : 'Add a to-do…'}
				bind:value={newTitle}
				maxlength={200}
				autocomplete="off"
			/>
			<Button type="submit" variant="primary">Add</Button>
		</form>

		<div class="filters">
			<div class="chips" role="group" aria-label="Show">
				{#each STATUS_FILTERS as filter (filter.value)}
					<button
						type="button"
						class="chip"
						style:--chip-accent="var(--color-butter)"
						aria-pressed={status === filter.value}
						onclick={() => (status = filter.value)}>{filter.label}</button
					>
				{/each}
			</div>
			{#if tags.length}
				<div class="chips" role="group" aria-label="Tag">
					{#each tags as t (t)}
						<button
							type="button"
							class="chip"
							style:--chip-accent="var(--color-sky)"
							aria-pressed={tag === t}
							onclick={() => (tag = tag === t ? null : t)}>#{t}</button
						>
					{/each}
				</div>
			{/if}
		</div>

		{#if error}<p class="error-box" role="alert">{error}</p>{/if}

		{#if !loaded}
			<ProgressBar label="Loading to-dos" />
		{:else if items.length === 0}
			<EmptyState
				message={status === 'done' ? 'Nothing finished yet' : 'All clear'}
				hint={status === 'done' ? undefined : 'Type above to add your first to-do.'}
			/>
		{:else}
			<ul class="list" bind:this={listEl}>
				{#each items as todo (todo.id)}
					<TodoRow
						{todo}
						ontoggle={toggle}
						onopen={(t) => editor.open({ kind: 'todo', todo: t })}
						draggable={canReorder}
						dragging={dragId === todo.id}
						ondragstart={(e) => startDrag(e, todo.id)}
					/>
				{/each}
			</ul>
		{/if}
	</Window>
</div>

<style>
	.page {
		max-width: 52rem;
	}

	.quick-add {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.filters {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1.25rem;
		margin-bottom: 1rem;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.error-box {
		margin-bottom: 1rem;
	}

	.list {
		list-style: none;
		margin: 0;
		padding: 0;
		border: 2px solid var(--color-ink);
	}
</style>
