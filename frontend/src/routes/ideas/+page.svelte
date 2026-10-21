<script lang="ts">
	import { ApiError } from '$lib/api';
	import { ideas as ideasApi } from '$lib/data';
	import { formatRelative } from '$lib/dates';
	import { editor } from '$lib/editor.svelte';
	import { markdownExcerpt } from '$lib/markdown';
	import { IDEA_STATUSES, type Idea, type IdeaStatus } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import EmptyState from '$lib/ui/EmptyState.svelte';
	import ProgressBar from '$lib/ui/ProgressBar.svelte';
	import Window from '$lib/ui/Window.svelte';

	type Filter = IdeaStatus | 'active' | 'all';
	const FILTERS: { value: Filter; label: string }[] = [
		{ value: 'active', label: 'Active' },
		...IDEA_STATUSES,
		{ value: 'all', label: 'All' }
	];
	const STATUS_LABEL = Object.fromEntries(IDEA_STATUSES.map((s) => [s.value, s.label]));

	let status = $state<Filter>('active');
	let tag = $state<string | null>(null);
	let query = $state('');
	let debouncedQuery = $state('');
	let list = $state<Idea[]>([]);
	let tags = $state<{ tag: string; count: number }[]>([]);
	let loaded = $state(false);
	let error = $state<string | null>(null);
	let jot = $state('');

	// Search as you type, without a request per keystroke.
	$effect(() => {
		const q = query;
		const timer = setTimeout(() => (debouncedQuery = q.trim()), 200);
		return () => clearTimeout(timer);
	});

	let latest = 0;
	$effect(() => {
		void editor.revision;
		const request = ++latest;
		Promise.all([ideasApi.list(status, tag ?? undefined, debouncedQuery || undefined), ideasApi.tags()]).then(
			([ideas, tagCounts]) => {
				if (request !== latest) return;
				list = ideas;
				tags = tagCounts;
				loaded = true;
				error = null;
			},
			(err) => {
				if (request !== latest) return;
				loaded = true;
				error = err instanceof ApiError ? err.message : 'Could not load ideas.';
			}
		);
	});

	async function quickJot(e: SubmitEvent) {
		e.preventDefault();
		const title = jot.trim();
		if (!title) return;
		try {
			await ideasApi.create({ title, body: '', tags: tag ? [tag] : [], status: 'new' });
			jot = '';
			editor.changed();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not save the idea.';
		}
	}
</script>

<svelte:head><title>Ideas · Life Planner</title></svelte:head>

<Window title="Ideas" accent="sky">
	<div class="top">
		<form class="jot" onsubmit={quickJot}>
			<label class="sr-only" for="jot">Jot an idea</label>
			<input id="jot" class="retro-input" placeholder="Jot an idea…" maxlength={120} autocomplete="off" bind:value={jot} />
			<Button type="submit" variant="primary">Save</Button>
			<Button onclick={() => editor.open({ kind: 'idea', title: jot.trim() || undefined })}>Write more…</Button>
		</form>
		<div class="search">
			<label class="sr-only" for="idea-search">Search ideas</label>
			<input
				id="idea-search"
				class="retro-input"
				type="search"
				placeholder="Search"
				aria-keyshortcuts="/"
				title="Search (press / on a keyboard)"
				data-search
				bind:value={query}
			/>
		</div>
	</div>

	<div class="filters">
		<div class="chips" role="group" aria-label="Status">
			{#each FILTERS as f (f.value)}
				<button
					type="button"
					class="chip"
					style:--chip-accent="var(--color-sky)"
					aria-pressed={status === f.value}
					onclick={() => (status = f.value)}>{f.label}</button
				>
			{/each}
		</div>
		{#if tags.length}
			<div class="chips" role="group" aria-label="Tag">
				{#each tags as t (t.tag)}
					<button
						type="button"
						class="chip"
						style:--chip-accent="var(--color-sky)"
						aria-pressed={tag === t.tag}
						onclick={() => (tag = tag === t.tag ? null : t.tag)}
						>#{t.tag} <span class="count">{t.count}</span></button
					>
				{/each}
			</div>
		{/if}
	</div>

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	{#if !loaded}
		<ProgressBar label="Loading ideas" />
	{:else if list.length === 0}
		<EmptyState
			message={debouncedQuery || tag ? 'No ideas match' : 'No ideas here yet'}
			hint={debouncedQuery || tag ? 'Try another search or tag.' : 'Jot one above.'}
		/>
	{:else}
		<ul class="grid">
			{#each list as idea (idea.id)}
				<li>
					<button type="button" class="card status-{idea.status}" onclick={() => editor.open({ kind: 'idea', idea })}>
						<span class="card-head">
							<span class="card-title">{idea.title}</span>
							<span class="badge status">{STATUS_LABEL[idea.status]}</span>
						</span>
						{#if idea.body.trim()}
							<span class="excerpt">{markdownExcerpt(idea.body)}</span>
						{/if}
						<span class="foot">
							<span class="tags">
								{#each idea.tags as t (t)}<span class="badge tag">#{t}</span>{/each}
							</span>
							<span class="updated">{formatRelative(idea.updated_at)}</span>
						</span>
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</Window>

<style>
	.top {
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.jot {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		gap: 0.5rem;
	}

	.jot :global(.btn:last-child) {
		grid-column: 1 / -1;
	}

	@media (min-width: 640px) {
		.jot {
			grid-template-columns: minmax(0, 1fr) auto auto;
		}

		.jot :global(.btn:last-child) {
			grid-column: auto;
		}
	}

	@media (min-width: 1024px) {
		.top {
			grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
		}
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

	.count {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--color-muted);
	}

	.error-box {
		margin-bottom: 1rem;
	}

	.grid {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		gap: 1rem;
	}

	@media (min-width: 768px) {
		.grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (min-width: 1280px) {
		.grid {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}

	.grid li {
		display: flex;
	}

	.card {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 0.75rem;
		font: inherit;
		color: inherit;
		text-align: left;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
		cursor: pointer;
	}

	.card:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}

	@media (hover: hover) {
		.card:hover {
			background: color-mix(in srgb, var(--color-sky) 15%, var(--color-surface));
		}
	}

	.card-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 0.5rem;
	}

	.card-title {
		font-family: var(--font-pixel);
		font-size: 1.1rem;
		line-height: 1.3;
		overflow-wrap: anywhere;
	}

	.status {
		flex-shrink: 0;
		--badge-accent: var(--color-sky);
	}

	.status-new .status {
		--badge-accent: var(--color-butter);
	}

	.status-done .status {
		--badge-accent: var(--color-mint);
	}

	.status-archived {
		background: var(--color-paper);
	}

	.status-archived .status {
		--badge-accent: var(--color-paper);
	}

	.excerpt {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
		font-size: 0.9rem;
		color: color-mix(in srgb, var(--color-ink) 80%, var(--color-surface));
	}

	.foot {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 0.5rem;
		margin-top: auto;
	}

	.tags {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem;
	}

	.tag {
		--badge-accent: color-mix(in srgb, var(--color-sky) 35%, var(--color-surface));
	}

	.updated {
		flex-shrink: 0;
		font-size: 0.75rem;
		color: var(--color-muted);
	}
</style>
