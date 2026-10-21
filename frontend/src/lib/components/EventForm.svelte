<script lang="ts">
	import { ApiError } from '$lib/api';
	import { events } from '$lib/data';
	import { addDays, parseLocal, toDateStr, toTimeStr } from '$lib/dates';
	import type { EventDraft } from '$lib/editor.svelte';
	import type { EventColor, EventInput, PlannerEvent } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import Checkbox from '$lib/ui/Checkbox.svelte';
	import ColorPicker from '$lib/ui/ColorPicker.svelte';
	import Select from '$lib/ui/Select.svelte';
	import TextArea from '$lib/ui/TextArea.svelte';
	import TextField from '$lib/ui/TextField.svelte';
	import FormActions from './FormActions.svelte';
	import { REPEATS, buildRrule, splitRrule } from './repeat';

	let {
		event,
		draft,
		onsaved,
		oncancel
	}: {
		event?: PlannerEvent;
		draft?: EventDraft;
		onsaved: () => void;
		oncancel: () => void;
	} = $props();

	// Form state is seeded once from the event (or draft) the sheet was opened with.
	// svelte-ignore state_referenced_locally
	const initial = seed(event, draft);
	let title = $state(initial.title);
	let notes = $state(initial.notes);
	let allDay = $state(initial.allDay);
	let startDate = $state(initial.startDate);
	let startTime = $state(initial.startTime);
	let endDate = $state(initial.endDate);
	let endTime = $state(initial.endTime);
	let repeat = $state(initial.repeat);
	let until = $state(initial.until);
	let color = $state<EventColor>(initial.color);

	let error = $state<string | null>(null);
	let busy = $state(false);

	const repeatOptions = $derived(
		REPEATS.some((r) => r.value === repeat) ? REPEATS : [...REPEATS, { value: repeat, label: `Custom (${repeat})` }]
	);

	function seed(event: PlannerEvent | undefined, draft: EventDraft | undefined) {
		if (event) {
			const start = parseLocal(event.start);
			const end = parseLocal(event.end);
			const { rule, until } = splitRrule(event.rrule);
			return {
				title: event.title,
				notes: event.notes,
				allDay: event.all_day,
				startDate: toDateStr(start),
				startTime: toTimeStr(start),
				// All-day ends are exclusive midnights; show the last day instead.
				endDate: toDateStr(event.all_day ? addDays(end, -1) : end),
				endTime: toTimeStr(end),
				repeat: rule,
				until,
				color: event.color ?? 'lavender'
			};
		}
		const startDate = draft?.startDate ?? toDateStr(new Date());
		const startTime = draft?.startTime ?? '09:00';
		const endTime = draft?.endTime ?? plusOneHour(startTime);
		return {
			title: '',
			notes: '',
			allDay: draft?.allDay ?? false,
			startDate,
			startTime,
			endDate: draft?.endDate ?? (endTime <= startTime ? toDateStr(addDays(parseLocal(startDate), 1)) : startDate),
			endTime,
			repeat: 'none',
			until: '',
			color: 'lavender' as EventColor
		};
	}

	function plusOneHour(time: string): string {
		const [h, m] = time.split(':').map(Number);
		return `${String((h + 1) % 24).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
	}

	function startOf(date: string, time: string) {
		return parseLocal(`${date}T${allDay ? '00:00' : time}:00`);
	}

	function endOf(date: string, time: string) {
		return allDay ? addDays(parseLocal(date), 1) : parseLocal(`${date}T${time}:00`);
	}

	// Moving the start drags the end along so the duration stays the same.
	let previousStart = startOf(initial.startDate, initial.startTime);
	function onStartChange() {
		if (!startDate || (!allDay && !startTime)) return;
		const newStart = startOf(startDate, startTime);
		const shift = newStart.getTime() - previousStart.getTime();
		const newEnd = new Date(endOf(endDate, endTime).getTime() + shift);
		endDate = toDateStr(allDay ? addDays(newEnd, -1) : newEnd);
		if (!allDay) endTime = toTimeStr(newEnd);
		previousStart = newStart;
	}

	function toInput(): EventInput | string {
		if (!title.trim()) return 'Give the event a title.';
		if (!startDate || !endDate) return 'Pick a start and end date.';
		const start = startOf(startDate, startTime);
		const end = endOf(endDate, endTime);
		if (end < start) return 'The event ends before it starts.';
		return {
			title: title.trim(),
			notes,
			start: `${toDateStr(start)}T${allDay ? '00:00' : startTime}:00`,
			end: allDay ? `${toDateStr(end)}T00:00:00` : `${endDate}T${endTime}:00`,
			all_day: allDay,
			rrule: buildRrule(repeat, until),
			color
		};
	}

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		const input = toInput();
		if (typeof input === 'string') {
			error = input;
			return;
		}
		busy = true;
		error = null;
		try {
			if (event) await events.update(event.id, input);
			else await events.create(input);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not save the event.';
		} finally {
			busy = false;
		}
	}

	async function remove() {
		if (!event) return;
		const what = event.rrule ? 'this event and all its repeats' : 'this event';
		if (!confirm(`Delete ${what}?`)) return;
		busy = true;
		try {
			await events.remove(event.id);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not delete the event.';
			busy = false;
		}
	}
</script>

<form onsubmit={submit} novalidate>
	<!-- svelte-ignore a11y_autofocus -->
	<TextField label="Title" bind:value={title} required autofocus={!event} maxlength={200} />

	<Checkbox bind:checked={allDay} onchange={() => (previousStart = startOf(startDate, startTime))}>
		All day
	</Checkbox>

	<div class="row">
		<TextField label="Starts" type="date" bind:value={startDate} onchange={onStartChange} required />
		{#if !allDay}
			<TextField label="Time" type="time" bind:value={startTime} onchange={onStartChange} required />
		{/if}
	</div>
	<div class="row">
		<TextField label="Ends" type="date" bind:value={endDate} min={startDate} required />
		{#if !allDay}
			<TextField label="Time" type="time" bind:value={endTime} required />
		{/if}
	</div>

	<div class="row">
		<Select label="Repeats" bind:value={repeat} options={repeatOptions} />
		{#if repeat !== 'none'}
			<TextField label="Until (optional)" type="date" bind:value={until} min={startDate} />
		{/if}
	</div>
	{#if event?.rrule}
		<p class="hint">Changes apply to every repeat of this event.</p>
	{/if}

	<ColorPicker label="Color" bind:value={color} />
	<TextArea label="Notes" bind:value={notes} />

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<FormActions>
		{#if event}
			<Button variant="danger" onclick={remove} disabled={busy}>Delete</Button>
		{/if}
		<span class="spacer"></span>
		<Button onclick={oncancel}>Cancel</Button>
		<Button type="submit" variant="primary" disabled={busy}>{event ? 'Save' : 'Add event'}</Button>
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

	.hint {
		margin: -0.5rem 0 0;
		font-size: 0.85rem;
		color: var(--color-muted);
	}

	.spacer {
		flex: 1;
	}
</style>
