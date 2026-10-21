<script lang="ts">
	import { ApiError } from '$lib/api';
	import { ideas as ideasApi } from '$lib/data';
	import { IDEA_STATUSES, type Idea, type IdeaInput, type IdeaStatus } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import Markdown from '$lib/ui/Markdown.svelte';
	import Select from '$lib/ui/Select.svelte';
	import TextField from '$lib/ui/TextField.svelte';
	import FormActions from './FormActions.svelte';

	let {
		idea,
		title: initialTitle,
		onsaved,
		oncancel
	}: {
		idea?: Idea;
		/** Prefill for a new idea, e.g. from the quick-jot box. */
		title?: string;
		onsaved: () => void;
		oncancel: () => void;
	} = $props();

	// Seeded once from the idea the sheet was opened with.
	// svelte-ignore state_referenced_locally
	let title = $state(idea?.title ?? initialTitle ?? '');
	// svelte-ignore state_referenced_locally
	let body = $state(idea?.body ?? '');
	// svelte-ignore state_referenced_locally
	let tagText = $state(idea?.tags.join(', ') ?? '');
	// svelte-ignore state_referenced_locally
	let status = $state<IdeaStatus>(idea?.status ?? 'new');

	let tab = $state<'write' | 'preview'>('write');
	let knownTags = $state<string[]>([]);
	let error = $state<string | null>(null);
	let busy = $state(false);

	const tabsId = $props.id();
	const tags = $derived(
		tagText
			.split(',')
			.map((t) => t.trim().replace(/^#/, '').toLowerCase())
			.filter(Boolean)
	);
	const suggestions = $derived(knownTags.filter((t) => !tags.includes(t)).slice(0, 8));

	$effect(() => {
		ideasApi.tags().then((list) => (knownTags = list.map((t) => t.tag)), () => {});
	});

	function addTag(tag: string) {
		tagText = [...tags, tag].join(', ');
	}

	async function save() {
		if (!title.trim()) {
			error = 'Give the idea a title.';
			return;
		}
		const input: IdeaInput = { title: title.trim(), body, tags, status };
		busy = true;
		error = null;
		try {
			if (idea) await ideasApi.update(idea.id, input);
			else await ideasApi.create(input);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not save the idea.';
		} finally {
			busy = false;
		}
	}

	async function remove() {
		if (!idea || !confirm('Delete this idea? Archiving keeps it out of the way instead.')) return;
		busy = true;
		try {
			await ideasApi.remove(idea.id);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not delete the idea.';
			busy = false;
		}
	}

	function onkeydown(e: KeyboardEvent) {
		// Ctrl/Cmd + Enter saves from anywhere in the form, including the notes.
		if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
			e.preventDefault();
			save();
		}
	}
</script>

<!-- The keydown listener catches Ctrl/Cmd+Enter bubbling up from any field. -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<form
	onsubmit={(e) => {
		e.preventDefault();
		save();
	}}
	{onkeydown}
	novalidate
>
	<!-- svelte-ignore a11y_autofocus -->
	<TextField label="Title" bind:value={title} maxlength={120} required autofocus={!idea} />

	<div class="row">
		<Select label="Status" bind:value={status} options={IDEA_STATUSES} />
		<TextField
			label="Tags (comma separated)"
			bind:value={tagText}
			placeholder="e.g. side project, home"
			autocapitalize="none"
		/>
	</div>
	{#if suggestions.length}
		<div class="suggest" role="group" aria-label="Add an existing tag">
			{#each suggestions as tag (tag)}
				<button type="button" class="badge add-tag" onclick={() => addTag(tag)}>+ #{tag}</button>
			{/each}
		</div>
	{/if}

	<div class="notes">
		<div class="tabs" role="tablist" aria-label="Notes">
			<span class="field-label">Notes</span>
			<button
				type="button"
				role="tab"
				id="{tabsId}-write"
				aria-selected={tab === 'write'}
				aria-controls="{tabsId}-panel"
				onclick={() => (tab = 'write')}>Write</button
			>
			<button
				type="button"
				role="tab"
				id="{tabsId}-preview"
				aria-selected={tab === 'preview'}
				aria-controls="{tabsId}-panel"
				onclick={() => (tab = 'preview')}>Preview</button
			>
		</div>
		<div id="{tabsId}-panel" role="tabpanel" aria-labelledby="{tabsId}-{tab}">
			{#if tab === 'write'}
				<textarea
					class="retro-input body"
					aria-label="Notes (Markdown)"
					rows={10}
					maxlength={20000}
					placeholder={'Markdown works: # heading, **bold**, - list, - [ ] checklist, [link](https://…)'}
					bind:value={body}
				></textarea>
			{:else}
				<div class="preview">
					{#if body.trim()}<Markdown source={body} />{:else}<p class="empty">Nothing to preview yet.</p>{/if}
				</div>
			{/if}
		</div>
		<p class="hint">Markdown supported · Ctrl/⌘ + Enter to save</p>
	</div>

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<FormActions>
		{#if idea}
			<Button variant="danger" onclick={remove} disabled={busy}>Delete</Button>
		{/if}
		<span class="spacer"></span>
		<Button onclick={oncancel}>Cancel</Button>
		<Button type="submit" variant="primary" disabled={busy}>{idea ? 'Save' : 'Add idea'}</Button>
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
		grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
		gap: 0.75rem;
	}

	.suggest {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		margin-top: -0.5rem;
	}

	.add-tag {
		--badge-accent: color-mix(in srgb, var(--color-sky) 35%, var(--color-surface));
		cursor: pointer;
	}

	.tabs {
		display: flex;
		align-items: flex-end;
		gap: 0.25rem;
	}

	.tabs .field-label {
		margin-right: auto;
	}

	[role='tab'] {
		padding: 0.2rem 0.75rem;
		font-family: var(--font-pixel);
		font-size: 0.85rem;
		color: var(--color-ink);
		background: var(--color-paper);
		border: 2px solid var(--color-ink);
		border-bottom: 0;
		cursor: pointer;
	}

	[role='tab'][aria-selected='true'] {
		background: var(--color-sky);
	}

	.body {
		display: block;
		resize: vertical;
		min-height: 12rem;
		font-size: 0.95rem;
		line-height: 1.5;
	}

	.preview {
		min-height: 12rem;
		padding: 0.75rem;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
	}

	.empty,
	.hint {
		margin: 0;
		font-size: 0.8rem;
		color: var(--color-muted);
	}

	.hint {
		margin-top: 0.3rem;
	}

	.spacer {
		flex: 1;
	}
</style>
