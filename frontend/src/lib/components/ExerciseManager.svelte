<script lang="ts">
	import { ApiError } from '$lib/api';
	import { exercises as exercisesApi } from '$lib/data';
	import { formatDay } from '$lib/dates';
	import { editor } from '$lib/editor.svelte';
	import { WORKOUT_KINDS, type Exercise, type WorkoutKind } from '$lib/types';

	let list = $state<Exercise[]>([]);
	let error = $state<string | null>(null);

	$effect(() => {
		void editor.revision;
		exercisesApi.list().then((l) => (list = l), (err) => (error = message(err)));
	});

	function message(err: unknown) {
		return err instanceof ApiError ? err.message : 'Something went wrong.';
	}

	async function update(exercise: Exercise, changes: { name?: string; kind?: WorkoutKind }) {
		if (changes.name !== undefined && !changes.name.trim()) return (error = 'Exercise names cannot be empty.');
		try {
			await exercisesApi.update(exercise.id, changes);
			error = null;
			editor.changed();
		} catch (err) {
			error = message(err);
		}
	}

	async function remove(exercise: Exercise) {
		if (!confirm(`Delete "${exercise.name}"?`)) return;
		try {
			await exercisesApi.remove(exercise.id);
			error = null;
			editor.changed();
		} catch (err) {
			error = message(err);
		}
	}
</script>

<p class="intro">
	Exercises are added automatically when you log them. Rename one here to fix a typo everywhere; only
	unused exercises can be deleted.
</p>

{#if error}<p class="error-box" role="alert">{error}</p>{/if}

{#if list.length === 0}
	<p class="intro">No exercises yet.</p>
{:else}
	<ul>
		{#each list as exercise (exercise.id)}
			<li>
				<input
					class="retro-input"
					aria-label="Exercise name"
					value={exercise.name}
					maxlength={60}
					onchange={(e) => update(exercise, { name: e.currentTarget.value.trim() })}
				/>
				<select
					class="retro-input"
					aria-label="{exercise.name} type"
					value={exercise.kind}
					onchange={(e) => update(exercise, { kind: e.currentTarget.value as WorkoutKind })}
				>
					{#each WORKOUT_KINDS as k (k.value)}<option value={k.value}>{k.label}</option>{/each}
				</select>
				<span class="usage">
					{exercise.times_logged
						? `${exercise.times_logged}× · last ${formatDay(exercise.last_done ?? '')}`
						: 'Unused'}
				</span>
				<button
					type="button"
					class="delete"
					aria-label="Delete {exercise.name}"
					disabled={exercise.times_logged > 0}
					title={exercise.times_logged > 0 ? 'In use: rename instead' : 'Delete'}
					onclick={() => remove(exercise)}>×</button
				>
			</li>
		{/each}
	</ul>
{/if}

<style>
	.intro {
		margin: 0 0 1rem;
		font-size: 0.85rem;
		color: var(--color-muted);
	}

	.error-box {
		margin-bottom: 1rem;
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	li {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 8rem 44px;
		grid-template-areas: 'name kind delete' 'usage usage usage';
		gap: 0.25rem 0.4rem;
		align-items: center;
	}

	li > input {
		grid-area: name;
	}

	li > select {
		grid-area: kind;
	}

	.usage {
		grid-area: usage;
		font-size: 0.75rem;
		color: var(--color-muted);
	}

	.delete {
		grid-area: delete;
		width: 44px;
		height: 44px;
		font-size: 1.2rem;
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		cursor: pointer;
	}

	.delete:disabled {
		color: var(--color-muted);
		border-color: var(--color-grid);
		cursor: not-allowed;
	}

	.delete:not(:disabled):hover {
		background: var(--color-rose);
	}
</style>
