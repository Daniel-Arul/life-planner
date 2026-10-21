<script lang="ts">
	import { ApiError } from '$lib/api';
	import { todos } from '$lib/data';
	import { PRIORITIES, type Priority, type Todo, type TodoInput } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import Checkbox from '$lib/ui/Checkbox.svelte';
	import Select from '$lib/ui/Select.svelte';
	import TextArea from '$lib/ui/TextArea.svelte';
	import TextField from '$lib/ui/TextField.svelte';
	import FormActions from './FormActions.svelte';

	let {
		todo,
		dueDate,
		onsaved,
		oncancel
	}: {
		todo?: Todo;
		dueDate?: string;
		onsaved: () => void;
		oncancel: () => void;
	} = $props();

	// Seeded once from the to-do (or default due date) the sheet was opened with.
	// svelte-ignore state_referenced_locally
	let title = $state(todo?.title ?? '');
	// svelte-ignore state_referenced_locally
	let due = $state(todo?.due_date ?? dueDate ?? '');
	// svelte-ignore state_referenced_locally
	let priority = $state<Priority>(todo?.priority ?? 0);
	// svelte-ignore state_referenced_locally
	let tag = $state(todo?.tag ?? '');
	// svelte-ignore state_referenced_locally
	let notes = $state(todo?.notes ?? '');
	// svelte-ignore state_referenced_locally
	let done = $state(todo?.status === 'done');

	let knownTags = $state<string[]>([]);
	let error = $state<string | null>(null);
	let busy = $state(false);

	const tagListId = $props.id();

	$effect(() => {
		todos.tags().then((tags) => (knownTags = tags), () => {});
	});

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		if (!title.trim()) {
			error = 'Give the to-do a title.';
			return;
		}
		const input: TodoInput = {
			title: title.trim(),
			notes,
			due_date: due || null,
			priority,
			tag: tag.trim() || null,
			status: done ? 'done' : 'open'
		};
		busy = true;
		error = null;
		try {
			if (todo) await todos.update(todo.id, input);
			else await todos.create(input);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not save the to-do.';
		} finally {
			busy = false;
		}
	}

	async function remove() {
		if (!todo || !confirm('Delete this to-do?')) return;
		busy = true;
		try {
			await todos.remove(todo.id);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not delete the to-do.';
			busy = false;
		}
	}
</script>

<form onsubmit={submit} novalidate>
	<!-- svelte-ignore a11y_autofocus -->
	<TextField label="Title" bind:value={title} required autofocus={!todo} maxlength={200} />

	<div class="row">
		<TextField label="Due (optional)" type="date" bind:value={due} />
		<Select label="Priority" bind:value={priority} options={PRIORITIES} />
	</div>

	<TextField
		label="Tag (optional)"
		bind:value={tag}
		list={tagListId}
		maxlength={50}
		autocapitalize="none"
		placeholder="e.g. home, work"
	/>
	<datalist id={tagListId}>
		{#each knownTags as known (known)}<option value={known}></option>{/each}
	</datalist>

	<TextArea label="Notes" bind:value={notes} />

	{#if todo}
		<Checkbox bind:checked={done}>Done</Checkbox>
	{/if}

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<FormActions>
		{#if todo}
			<Button variant="danger" onclick={remove} disabled={busy}>Delete</Button>
		{/if}
		<span class="spacer"></span>
		<Button onclick={oncancel}>Cancel</Button>
		<Button type="submit" variant="primary" disabled={busy}>{todo ? 'Save' : 'Add to-do'}</Button>
	</FormActions>
</form>

<style>
	form {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
		gap: 0.75rem;
	}

	.spacer {
		flex: 1;
	}
</style>
