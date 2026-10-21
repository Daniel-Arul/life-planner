<script lang="ts">
	import { ApiError } from '$lib/api';
	import { exercises as exercisesApi, workouts as workoutsApi } from '$lib/data';
	import { todayStr } from '$lib/dates';
	import { WORKOUT_KINDS, type Exercise, type Workout, type WorkoutInput, type WorkoutKind } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import Select from '$lib/ui/Select.svelte';
	import TextArea from '$lib/ui/TextArea.svelte';
	import TextField from '$lib/ui/TextField.svelte';
	import { distanceUnit, formatDuration, parseDuration, weightUnit } from '$lib/units';
	import FormActions from './FormActions.svelte';

	let {
		workout,
		date,
		onsaved,
		oncancel
	}: {
		workout?: Workout;
		date?: string;
		onsaved: () => void;
		oncancel: () => void;
	} = $props();

	/** Form rows hold raw strings so half-typed numbers don't get mangled. */
	type Row = {
		key: number;
		exercise: string;
		sets: string;
		reps: string;
		weight: string;
		distance: string;
		time: string;
	};

	let nextKey = 0;
	const blankRow = (): Row => ({ key: nextKey++, exercise: '', sets: '', reps: '', weight: '', distance: '', time: '' });
	const toRows = (w: Workout): Row[] =>
		w.entries.map((e) => ({
			key: nextKey++,
			exercise: e.exercise_name,
			sets: e.reps !== null || e.sets > 1 ? String(e.sets) : '',
			reps: e.reps?.toString() ?? '',
			weight: e.weight?.toString() ?? '',
			distance: e.distance?.toString() ?? '',
			time: e.duration_s !== null ? formatDuration(e.duration_s) : ''
		}));

	// Seeded once from the workout (or default date) the sheet was opened with.
	// svelte-ignore state_referenced_locally
	let performedOn = $state(workout?.performed_on ?? date ?? todayStr());
	// svelte-ignore state_referenced_locally
	let kind = $state<WorkoutKind>(workout?.kind ?? 'strength');
	// svelte-ignore state_referenced_locally
	let title = $state(workout?.title ?? '');
	// svelte-ignore state_referenced_locally
	let duration = $state(workout?.duration_min?.toString() ?? '');
	// svelte-ignore state_referenced_locally
	let notes = $state(workout?.notes ?? '');
	// svelte-ignore state_referenced_locally
	let rows = $state<Row[]>(workout && workout.entries.length ? toRows(workout) : [blankRow()]);

	let library = $state<Exercise[]>([]);
	let recent = $state<Workout[]>([]);
	let error = $state<string | null>(null);
	let busy = $state(false);

	const listId = $props.id();
	const cardio = $derived(kind === 'cardio');

	// The most recent other workout with the same title (or, untitled, the same kind).
	const previous = $derived(
		recent.find(
			(w) =>
				w.id !== workout?.id &&
				w.entries.length > 0 &&
				(title.trim() ? w.title.toLowerCase() === title.trim().toLowerCase() : w.kind === kind)
		)
	);

	$effect(() => {
		exercisesApi.list().then((l) => (library = l), () => {});
		workoutsApi.list(30).then((l) => (recent = l), () => {});
	});

	function copyPrevious() {
		if (!previous) return;
		rows = toRows(previous);
		if (!title.trim()) title = previous.title;
		if (!duration && previous.duration_min) duration = String(previous.duration_min);
	}

	function num(text: string, field: string, int = false): number | null {
		const t = text.trim().replace(',', '.');
		if (!t) return null;
		const n = Number(t);
		if (!Number.isFinite(n) || n < 0 || (int && !Number.isInteger(n))) throw new Error(`${field} "${text}" isn't a valid number.`);
		return n;
	}

	function toInput(): WorkoutInput {
		const filled = rows.filter((r) => [r.exercise, r.sets, r.reps, r.weight, r.distance, r.time].some((v) => v.trim()));
		const entries = filled.map((r) => {
			if (!r.exercise.trim()) throw new Error('Every row needs an exercise name.');
			const durationS = parseDuration(r.time);
			if (durationS === undefined) throw new Error(`Time "${r.time}" should look like 28:00 or 45.`);
			return {
				exercise_name: r.exercise.trim(),
				sets: num(r.sets, 'Sets', true) ?? 1,
				reps: num(r.reps, 'Reps', true),
				weight: num(r.weight, 'Weight'),
				distance: num(r.distance, 'Distance'),
				duration_s: durationS
			};
		});
		if (entries.some((e) => e.sets < 1)) throw new Error('Sets must be at least 1.');
		return {
			performed_on: performedOn,
			kind,
			title: title.trim(),
			duration_min: num(duration, 'Duration', true),
			notes,
			entries
		};
	}

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		let input: WorkoutInput;
		try {
			input = toInput();
		} catch (err) {
			error = (err as Error).message;
			return;
		}
		busy = true;
		error = null;
		try {
			if (workout) await workoutsApi.replace(workout.id, input);
			else await workoutsApi.create(input);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not save the workout.';
		} finally {
			busy = false;
		}
	}

	async function remove() {
		if (!workout || !confirm('Delete this workout?')) return;
		busy = true;
		try {
			await workoutsApi.remove(workout.id);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not delete the workout.';
			busy = false;
		}
	}
</script>

<form onsubmit={submit} novalidate>
	<div class="row">
		<TextField label="Date" type="date" bind:value={performedOn} required />
		<Select label="Type" bind:value={kind} options={WORKOUT_KINDS} />
	</div>
	<div class="row">
		<TextField label="Name (optional)" bind:value={title} maxlength={80} placeholder="e.g. Push day" />
		<TextField label="Minutes (optional)" bind:value={duration} inputmode="numeric" placeholder="45" />
	</div>

	<fieldset class="entries">
		<legend class="field-label">Exercises</legend>
		{#if previous && !workout}
			<button type="button" class="copy" onclick={copyPrevious}>
				↻ Same as last time ({previous.title || previous.kind}, {previous.entries.length}
				{previous.entries.length === 1 ? 'exercise' : 'exercises'})
			</button>
		{/if}

		<!-- Column headings, since placeholders vanish once a field is filled. -->
		<div class="entry head" class:cardio aria-hidden="true">
			<span class="exercise">Exercise</span>
			{#if cardio}
				<span>{distanceUnit()}</span><span>Time</span>
			{:else}
				<span>Sets</span><span>Reps</span><span>{weightUnit()}</span>
			{/if}
		</div>
		{#each rows as row, i (row.key)}
			<div class="entry" class:cardio>
				<input
					class="retro-input exercise"
					aria-label="Exercise {i + 1}"
					placeholder="Exercise"
					list={listId}
					maxlength={60}
					autocapitalize="words"
					bind:value={row.exercise}
				/>
				{#if cardio}
					<input class="retro-input" aria-label="Distance ({distanceUnit()})" placeholder={distanceUnit()} inputmode="decimal" bind:value={row.distance} />
					<input class="retro-input" aria-label="Time" placeholder="mm:ss" inputmode="numeric" bind:value={row.time} />
				{:else}
					<input class="retro-input" aria-label="Sets" placeholder="sets" inputmode="numeric" bind:value={row.sets} />
					<input class="retro-input" aria-label="Reps" placeholder="reps" inputmode="numeric" bind:value={row.reps} />
					<input class="retro-input" aria-label="Weight ({weightUnit()})" placeholder={weightUnit()} inputmode="decimal" bind:value={row.weight} />
				{/if}
				<button
					type="button"
					class="remove"
					aria-label="Remove exercise {i + 1}"
					onclick={() => (rows = rows.length > 1 ? rows.filter((r) => r.key !== row.key) : [blankRow()])}
				>×</button>
			</div>
		{/each}
		<datalist id={listId}>
			{#each library as ex (ex.id)}<option value={ex.name}></option>{/each}
		</datalist>
		<Button onclick={() => (rows = [...rows, blankRow()])}>+ Add exercise</Button>
	</fieldset>

	<TextArea label="Notes" bind:value={notes} rows={2} />

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<FormActions>
		{#if workout}
			<Button variant="danger" onclick={remove} disabled={busy}>Delete</Button>
		{/if}
		<span class="spacer"></span>
		<Button onclick={oncancel}>Cancel</Button>
		<Button type="submit" variant="primary" disabled={busy}>{workout ? 'Save' : 'Log workout'}</Button>
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

	.entries {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin: 0;
		padding: 0;
		border: 0;
		min-width: 0;
	}

	legend {
		padding: 0;
		margin-bottom: 0.25rem;
	}

	/* Phone: exercise on its own line, numbers + remove beneath. */
	.entry {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr)) 44px;
		gap: 0.4rem;
		padding-bottom: 0.5rem;
		border-bottom: 2px dotted var(--color-grid);
	}

	.entry.cardio {
		grid-template-columns: repeat(2, minmax(0, 1fr)) 44px;
	}

	.entry .exercise {
		grid-column: 1 / -1;
	}

	.entry .retro-input {
		padding-inline: 0.5rem;
	}

	.entry.head {
		padding-bottom: 0;
		border-bottom: 0;
		font-family: var(--font-pixel);
		font-size: 0.8rem;
		color: var(--color-muted);
	}

	/* On phones the exercise name has its own line, so its heading isn't needed. */
	.entry.head .exercise {
		display: none;
	}

	@media (min-width: 768px) {
		.entry {
			grid-template-columns: minmax(0, 2.2fr) repeat(3, minmax(0, 1fr)) 44px;
		}

		.entry.cardio {
			grid-template-columns: minmax(0, 2.2fr) repeat(2, minmax(0, 1fr)) 44px;
		}

		.entry .exercise {
			grid-column: auto;
		}

		.entry.head .exercise {
			display: block;
		}
	}

	.remove {
		height: 44px;
		font-size: 1.2rem;
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		cursor: pointer;
	}

	.copy {
		align-self: flex-start;
		padding: 0.4rem 0.75rem;
		font: inherit;
		font-size: 0.85rem;
		color: var(--color-ink);
		background: color-mix(in srgb, var(--color-mint) 50%, var(--color-surface));
		border: 2px dashed var(--color-ink);
		cursor: pointer;
	}

	.spacer {
		flex: 1;
	}
</style>
