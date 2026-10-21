<script lang="ts">
	import { Calendar, DayGrid, Interaction, List, TimeGrid } from '@event-calendar/core';
	import '@event-calendar/core/index.css';
	import { MediaQuery } from 'svelte/reactivity';
	import { ApiError } from '$lib/api';
	import { events as eventsApi, fetchCalendar, todos as todosApi } from '$lib/data';
	import { addDays, parseLocal, toDateStr, toLocalISO, toTimeStr } from '$lib/dates';
	import { editor } from '$lib/editor.svelte';
	import type { CalendarItem } from '$lib/types';
	import Window from '$lib/ui/Window.svelte';

	type Kind = CalendarItem['kind'];
	type CalendarApi = { next(): unknown; prev(): unknown; unselect(): unknown };

	const KINDS: { kind: Kind; label: string; accent: string }[] = [
		{ kind: 'event', label: 'Events', accent: 'lavender' },
		{ kind: 'todo', label: 'To-dos', accent: 'butter' }
	];

	const laptop = new MediaQuery('min-width: 1024px');
	// Drag-to-create and drag-to-move only where there's a mouse; touch gets taps.
	const canHover = new MediaQuery('hover: hover');

	// The library types bind:this as a plain component; its instance exposes next/prev/unselect.
	let calendarRef = $state<unknown>();
	const ec = $derived(calendarRef as CalendarApi | undefined);
	let items = $state<CalendarItem[]>([]);
	let range = $state<{ start: Date; end: Date } | null>(null);
	let shown = $state<Record<Kind, boolean>>({ event: true, todo: true });
	let error = $state<string | null>(null);

	const options = $state<Calendar.Options>({
		view: laptop.current ? 'dayGridMonth' : 'listWeek',
		headerToolbar: {
			start: 'prev,next today',
			center: 'title',
			end: laptop.current ? 'dayGridMonth,timeGridWeek,listWeek' : 'listWeek,timeGridDay,dayGridMonth'
		},
		buttonText: (text) => ({
			...text,
			today: 'Today',
			dayGridMonth: 'Month',
			timeGridWeek: 'Week',
			timeGridDay: 'Day',
			listWeek: 'Agenda'
		}),
		height: '70dvh',
		views: { dayGridMonth: { height: 'auto' }, listWeek: { height: 'auto' } },
		dayMaxEvents: true,
		nowIndicator: true,
		scrollTime: '07:00:00',
		noEventsContent: 'Nothing planned this week',
		events: [],
		datesSet: (info) => {
			range = { start: info.start, end: info.end };
		},
		dateClick: (info) => {
			editor.open({
				kind: 'chooser',
				date: toDateStr(info.date),
				time: info.allDay ? undefined : toTimeStr(info.date)
			});
		},
		select: (info) => {
			ec?.unselect();
			const span = info.end.getTime() - info.start.getTime();
			// A plain click also "selects" one cell; dateClick already handles that.
			if (span <= (info.allDay ? 86_400_000 : 30 * 60_000)) return;
			editor.open({
				kind: 'event',
				draft: info.allDay
					? { allDay: true, startDate: toDateStr(info.start), endDate: toDateStr(addDays(info.end, -1)) }
					: {
							startDate: toDateStr(info.start),
							startTime: toTimeStr(info.start),
							endDate: toDateStr(info.end),
							endTime: toTimeStr(info.end)
						}
			});
		},
		eventClick: (info) => {
			const item = info.event.extendedProps.item as CalendarItem;
			const open = item.kind === 'event' ? editor.editEvent(item.source_id) : editor.editTodo(item.source_id);
			open.catch((err) => (error = message(err, 'Could not open that item.')));
		},
		eventDrop: async (info) => {
			const item = info.event.extendedProps.item as CalendarItem;
			const { start, allDay } = info.event;
			try {
				if (item.kind === 'todo') {
					await todosApi.update(item.source_id, { due_date: toDateStr(start) });
				} else {
					// Moving between the all-day row and the time grid resets the length.
					const end =
						allDay === item.all_day
							? info.event.end
							: allDay
								? addDays(start, 1)
								: new Date(start.getTime() + 60 * 60_000);
					await eventsApi.update(item.source_id, {
						start: toLocalISO(start),
						end: toLocalISO(end),
						all_day: allDay
					});
				}
				editor.changed();
			} catch (err) {
				info.revert();
				error = message(err, 'Could not move that item.');
			}
		},
		eventResize: async (info) => {
			const item = info.event.extendedProps.item as CalendarItem;
			try {
				await eventsApi.update(item.source_id, { end: toLocalISO(info.event.end) });
				editor.changed();
			} catch (err) {
				info.revert();
				error = message(err, 'Could not resize that event.');
			}
		}
	});

	function message(err: unknown, fallback: string) {
		return err instanceof ApiError ? err.message : fallback;
	}

	$effect(() => {
		options.selectable = canHover.current;
		options.editable = canHover.current;
	});

	// Refetch when the visible range changes or anything is saved elsewhere.
	let latest = 0;
	$effect(() => {
		void editor.revision;
		if (!range) return;
		const request = ++latest;
		fetchCalendar(range.start, range.end).then(
			(result) => {
				if (request !== latest) return;
				items = result;
				error = null;
			},
			(err) => {
				if (request === latest) error = message(err, 'Could not load the calendar.');
			}
		);
	});

	$effect(() => {
		options.events = items
			.filter((item) => shown[item.kind])
			.map((item) => ({
				id: item.id,
				title: item.title,
				start: parseLocal(item.start),
				end: parseLocal(item.end),
				allDay: item.all_day,
				backgroundColor: `var(--color-${item.color})`,
				textColor: 'var(--color-ink)',
				// Repeats are edited through the form, so their occurrences don't drag.
				startEditable: !item.recurring,
				durationEditable: item.kind === 'event' && !item.recurring,
				classNames: [`kind-${item.kind}`, ...(item.done ? ['is-done'] : [])],
				extendedProps: { item }
			}));
	});

	// Swipe left/right on phones to change week/day/month.
	let touchStart: { x: number; y: number } | null = null;
	function ontouchstart(e: TouchEvent) {
		const t = e.touches[0];
		touchStart = { x: t.clientX, y: t.clientY };
	}
	function ontouchend(e: TouchEvent) {
		if (!touchStart || laptop.current) return;
		const t = e.changedTouches[0];
		const dx = t.clientX - touchStart.x;
		const dy = t.clientY - touchStart.y;
		touchStart = null;
		if (Math.abs(dx) > 60 && Math.abs(dy) < 40) {
			if (dx < 0) ec?.next();
			else ec?.prev();
		}
	}
</script>

<svelte:head><title>Calendar · Life Planner</title></svelte:head>

<Window title="Calendar" accent="lavender">
	<div class="kinds" role="group" aria-label="Show on calendar">
		{#each KINDS as { kind, label, accent } (kind)}
			<button
				type="button"
				class="chip"
				style:--chip-accent="var(--color-{accent})"
				aria-pressed={shown[kind]}
				onclick={() => (shown[kind] = !shown[kind])}
			>
				<span class="swatch" aria-hidden="true"></span>
				{label}
			</button>
		{/each}
	</div>

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<div class="cal" role="region" aria-label="Calendar" {ontouchstart} {ontouchend}>
		<Calendar bind:this={calendarRef} plugins={[DayGrid, TimeGrid, List, Interaction]} {options}>
			{#snippet eventContent({ event, timeText }: Calendar.EventContentInfo)}
				{@const item = event.extendedProps.item as CalendarItem}
				<span class="ev">
					{#if item.kind === 'todo'}
						<span class="tick" class:checked={item.done} aria-label={item.done ? 'done' : 'to-do'}></span>
					{/if}
					{#if timeText && !item.all_day}<span class="time">{timeText}</span>{/if}
					<span class="ev-title">{item.title}</span>
					{#if item.recurring}<span class="repeat" title="Repeats">↻</span>{/if}
				</span>
			{/snippet}
		</Calendar>
	</div>
</Window>

<style>
	.kinds {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin-bottom: 1rem;
	}

	.swatch {
		width: 0.7rem;
		height: 0.7rem;
		border: 2px solid var(--color-ink);
		background: var(--color-surface);
	}

	.chip[aria-pressed='true'] .swatch {
		background: var(--color-ink);
	}

	.error-box {
		margin-bottom: 1rem;
	}

	/* --- Retro theme for @event-calendar --- */
	.cal :global(.ec) {
		--ec-bg-color: var(--color-surface);
		--ec-border-color: color-mix(in srgb, var(--color-ink) 28%, transparent);
		--ec-button-bg-color: var(--color-surface);
		--ec-button-border-color: var(--color-ink);
		--ec-button-active-bg-color: var(--color-lavender);
		--ec-button-active-border-color: var(--color-ink);
		--ec-today-bg-color: color-mix(in srgb, var(--color-butter) 45%, var(--color-surface));
		--ec-highlight-color: color-mix(in srgb, var(--color-lavender) 35%, var(--color-surface));
		--ec-event-text-color: var(--color-ink);
		--ec-now-indicator-color: var(--color-alert);
		--ec-popup-bg-color: var(--color-surface);
		font-family: var(--font-mono);
		font-size: 0.85rem;
	}

	.cal :global(.ec-toolbar) {
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.cal :global(.ec-title) {
		font-family: var(--font-pixel);
		font-size: 1.2rem;
		font-weight: 500;
		margin: 0;
	}

	.cal :global(.ec-button) {
		min-height: 38px;
		font-family: var(--font-pixel);
		font-size: 0.9rem;
		color: var(--color-ink);
		border-width: 2px;
		border-radius: 0;
	}

	.cal :global(.ec-button:active) {
		transform: translate(1px, 1px);
	}

	.cal :global(.ec-day-head),
	.cal :global(.ec-col-head) {
		font-family: var(--font-pixel);
	}

	.cal :global(.ec-event) {
		border: 2px solid var(--color-ink);
		border-radius: 0;
		box-shadow: none;
		cursor: pointer;
	}

	.cal :global(.ec-list .ec-event) {
		border: 0;
	}

	.cal :global(.ec-event.is-done .ev-title) {
		text-decoration: line-through;
		color: var(--color-muted);
	}

	/* Today's cell gets a blinking dashed outline, like a text cursor. */
	.cal :global(.ec-day.ec-today) {
		outline: 2px dashed var(--color-ink);
		outline-offset: -3px;
		animation: blink 1.2s steps(1) infinite;
	}

	.cal :global(.ec-list .ec-day.ec-today) {
		outline: none;
		animation: none;
	}

	@keyframes blink {
		50% {
			outline-color: transparent;
		}
	}

	.ev {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		min-width: 0;
		overflow: hidden;
	}

	.time {
		font-weight: 600;
		flex-shrink: 0;
	}

	.ev-title {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.tick {
		flex-shrink: 0;
		width: 0.7rem;
		height: 0.7rem;
		border: 2px solid var(--color-ink);
		background: var(--color-surface);
	}

	.tick.checked {
		background: var(--color-ink);
	}

	.repeat {
		flex-shrink: 0;
	}
</style>
