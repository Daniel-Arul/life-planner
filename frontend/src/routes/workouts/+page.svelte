<script lang="ts">
	import { ApiError } from '$lib/api';
	import { exercises as exercisesApi, workouts as workoutsApi } from '$lib/data';
	import { formatDay, parseLocal, todayStr } from '$lib/dates';
	import { editor } from '$lib/editor.svelte';
	import type { Exercise, ProgressPoint, Workout, WorkoutStats } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import ColumnChart from '$lib/ui/ColumnChart.svelte';
	import EmptyState from '$lib/ui/EmptyState.svelte';
	import LineChart from '$lib/ui/LineChart.svelte';
	import ProgressBar from '$lib/ui/ProgressBar.svelte';
	import StatTile from '$lib/ui/StatTile.svelte';
	import Window from '$lib/ui/Window.svelte';
	import {
		distanceUnit,
		formatDuration,
		formatNumber,
		kindLabel,
		summarizeEntry,
		weightUnit
	} from '$lib/units';

	type Metric = 'best_weight' | 'volume' | 'max_reps' | 'distance' | 'duration_s';
	const METRICS: Record<Metric, { label: string; format: (v: number) => string }> = {
		best_weight: { label: 'Best weight', format: (v) => `${formatNumber(v)} ${weightUnit()}` },
		volume: { label: 'Volume', format: (v) => `${formatNumber(Math.round(v))} ${weightUnit()}` },
		max_reps: { label: 'Most reps', format: (v) => `${formatNumber(v)} reps` },
		distance: { label: 'Distance', format: (v) => `${formatNumber(v)} ${distanceUnit()}` },
		duration_s: { label: 'Time', format: (v) => formatDuration(Math.round(v)) }
	};

	let stats = $state<WorkoutStats | null>(null);
	let log = $state<Workout[]>([]);
	let library = $state<Exercise[]>([]);
	let loaded = $state(false);
	let error = $state<string | null>(null);

	let exerciseId = $state<number | null>(null);
	let progress = $state<ProgressPoint[]>([]);
	let metric = $state<Metric>('best_weight');

	const logged = $derived(library.filter((e) => e.times_logged > 0));
	const selected = $derived(logged.find((e) => e.id === exerciseId));
	// Only offer metrics this exercise actually has data for.
	const metrics = $derived(
		(Object.keys(METRICS) as Metric[]).filter((m) => progress.some((p) => (p[m] ?? 0) > 0))
	);
	const series = $derived(
		progress
			.filter((p) => (p[metric] ?? 0) > 0)
			.map((p) => ({ date: p.date, value: p[metric] as number, key: String(p.workout_id) }))
	);

	$effect(() => {
		void editor.revision;
		Promise.all([workoutsApi.stats(12), workoutsApi.list(30), exercisesApi.list()]).then(
			([s, l, ex]) => {
				stats = s;
				log = l;
				library = ex;
				loaded = true;
				error = null;
				// Default to the most recently trained exercise.
				if (exerciseId === null || !ex.some((e) => e.id === exerciseId && e.times_logged)) {
					const latest = ex
						.filter((e) => e.last_done)
						.sort((a, b) => (b.last_done ?? '').localeCompare(a.last_done ?? ''))[0];
					exerciseId = latest?.id ?? null;
				}
			},
			(err) => {
				loaded = true;
				error = err instanceof ApiError ? err.message : 'Could not load workouts.';
			}
		);
	});

	$effect(() => {
		void editor.revision;
		if (exerciseId === null) return;
		const id = exerciseId;
		workoutsApi.progress(id).then((points) => {
			if (id !== exerciseId) return;
			progress = points;
			const available = (Object.keys(METRICS) as Metric[]).filter((m) =>
				points.some((p) => (p[m] ?? 0) > 0)
			);
			if (!available.includes(metric)) metric = available[0] ?? 'best_weight';
		});
	});

	const weekLabel = (d: string) =>
		parseLocal(d).toLocaleDateString([], { month: 'short', day: 'numeric' });

	function openWorkout(key: string) {
		const found = log.find((w) => String(w.id) === key);
		if (found) editor.open({ kind: 'workout', workout: found });
		else editor.editWorkout(Number(key));
	}
</script>

<svelte:head><title>Workouts · Life Planner</title></svelte:head>

<div class="page">
	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<div class="tiles">
		<StatTile
			label="This week"
			value={String(stats?.this_week_workouts ?? '–')}
			note={stats?.this_week_workouts === 1 ? 'workout' : 'workouts'}
		/>
		<StatTile label="Minutes" value={String(stats?.this_week_minutes ?? '–')} note="this week" />
		<StatTile
			label="Streak"
			value={String(stats?.streak_weeks ?? '–')}
			note={stats?.streak_weeks === 1 ? 'week in a row' : 'weeks in a row'}
		/>
	</div>

	<div class="layout">
		<div class="log">
			<Window title="Log" accent="mint">
				<Button variant="primary" onclick={() => editor.open({ kind: 'workout', date: todayStr() })}>
					+ Log workout
				</Button>
				{#if !loaded}
					<ProgressBar label="Loading workouts" />
				{:else if log.length === 0}
					<EmptyState message="No workouts yet" hint="Log your first one above." />
				{:else}
					<ul class="cards">
						{#each log as workout (workout.id)}
							<li>
								<button type="button" class="card" onclick={() => editor.open({ kind: 'workout', workout })}>
									<span class="card-head">
										<span class="card-title">{workout.title || `${kindLabel(workout.kind)} workout`}</span>
										<span class="card-date">{formatDay(workout.performed_on)}</span>
									</span>
									<span class="meta">
										<span class="badge kind">{kindLabel(workout.kind)}</span>
										{#if workout.duration_min}<span class="badge">{workout.duration_min} min</span>{/if}
									</span>
									{#if workout.entries.length}
										<span class="entries">
											{#each workout.entries as entry (entry.id)}
												<span class="entry">
													<span class="ex">{entry.exercise_name}</span>
													<span class="tabular">{summarizeEntry(entry)}</span>
												</span>
											{/each}
										</span>
									{/if}
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</Window>
		</div>

		<div class="weekly">
			<Window title="Workouts per week" accent="mint">
				{#if stats}
					<ColumnChart
						columns={stats.weeks.map((w) => ({
							key: w.week_start,
							value: w.workouts,
							label: `Week of ${weekLabel(w.week_start)}`,
							tick: weekLabel(w.week_start)
						}))}
						formatValue={(v) => `${v} ${v === 1 ? 'workout' : 'workouts'}`}
						formatTick={(v) => String(v)}
						label="Workouts per week, last 12 weeks"
						color="var(--color-mint-deep)"
						integer
						showTick={(i) => i % 3 === 0 || i === stats!.weeks.length - 1}
					/>
				{/if}
			</Window>
		</div>

		<div class="progress">
			<Window title="Progress" accent="mint">
				{#if logged.length === 0}
					<EmptyState message="Nothing to chart yet" hint="Log an exercise twice to see a trend." />
				{:else}
					<div class="controls">
						<label class="field-label" for="exercise-pick">Exercise</label>
						<select id="exercise-pick" class="retro-input" bind:value={exerciseId}>
							{#each logged as ex (ex.id)}
								<option value={ex.id}>{ex.name} ({ex.times_logged})</option>
							{/each}
						</select>
						{#if metrics.length > 1}
							<div class="chips" role="group" aria-label="Measure">
								{#each metrics as m (m)}
									<button
										type="button"
										class="chip"
										style:--chip-accent="var(--color-mint)"
										aria-pressed={metric === m}
										onclick={() => (metric = m)}>{METRICS[m].label}</button
									>
								{/each}
							</div>
						{/if}
					</div>
					{#if series.length === 0}
						<EmptyState message="No numbers logged for this exercise" />
					{:else}
						<h3 class="chart-title">{selected?.name} · {METRICS[metric].label}</h3>
						<LineChart
							points={series}
							formatValue={METRICS[metric].format}
							label="{selected?.name}, {METRICS[metric].label}"
							onselect={openWorkout}
						/>
						{#if series.length === 1}
							<p class="hint">One session so far; the trend line appears after the next.</p>
						{/if}
					{/if}
				{/if}
			</Window>
		</div>
	</div>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.tiles {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.75rem;
	}

	.layout {
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		grid-template-areas: 'log' 'weekly' 'progress';
		gap: 1rem;
	}

	.log {
		grid-area: log;
	}

	.weekly {
		grid-area: weekly;
	}

	.progress {
		grid-area: progress;
	}

	@media (min-width: 1024px) {
		.layout {
			grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
			grid-template-areas: 'weekly log' 'progress log';
			grid-template-rows: auto 1fr;
			gap: 1.5rem;
			align-items: start;
		}

		.tiles {
			gap: 1.5rem;
		}
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.cards {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.card {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		width: 100%;
		padding: 0.6rem 0.75rem;
		font: inherit;
		color: inherit;
		text-align: left;
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		border-left-width: 8px;
		border-left-color: var(--color-mint);
		cursor: pointer;
	}

	@media (hover: hover) {
		.card:hover {
			background: color-mix(in srgb, var(--color-mint) 20%, var(--color-surface));
		}
	}

	.card-head {
		display: flex;
		justify-content: space-between;
		gap: 0.5rem;
		align-items: baseline;
	}

	.card-title {
		font-family: var(--font-pixel);
		font-size: 1.05rem;
	}

	.card-date {
		flex-shrink: 0;
		font-size: 0.85rem;
		color: var(--color-muted);
	}

	.meta {
		display: flex;
		gap: 0.4rem;
	}

	.kind {
		--badge-accent: var(--color-mint);
	}

	.entries {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		font-size: 0.9rem;
	}

	.entry {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 0 0.75rem;
		padding-top: 0.15rem;
		border-top: 2px dotted var(--color-grid);
	}

	.ex {
		font-weight: 600;
	}

	.controls {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		margin-bottom: 1rem;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin-top: 0.4rem;
	}

	.chart-title {
		margin: 0 0 0.75rem;
		font-size: 0.95rem;
	}

	.hint {
		margin: 0.5rem 0 0;
		font-size: 0.8rem;
		color: var(--color-muted);
	}
</style>
