// Shapes of the backend's JSON. Date-times are local wall-clock ISO strings
// without a timezone ("2026-10-21T09:00:00"); dates are "YYYY-MM-DD".

export type EventColor = 'lavender' | 'mint' | 'peach' | 'butter' | 'sky' | 'rose';

export type Priority = 0 | 1 | 2 | 3;

export const PRIORITIES: { value: Priority; label: string }[] = [
	{ value: 0, label: 'None' },
	{ value: 1, label: 'Low' },
	{ value: 2, label: 'Medium' },
	{ value: 3, label: 'High' }
];

export type Todo = {
	id: number;
	title: string;
	notes: string;
	due_date: string | null;
	priority: Priority;
	tag: string | null;
	status: 'open' | 'done';
	completed_at: string | null;
	position: number;
};

export type TodoInput = Pick<Todo, 'title' | 'notes' | 'due_date' | 'priority' | 'tag'> & {
	status?: Todo['status'];
};

export type PlannerEvent = {
	id: number;
	title: string;
	notes: string;
	start: string;
	end: string;
	all_day: boolean;
	rrule: string | null;
	color: EventColor | null;
};

export type EventInput = Omit<PlannerEvent, 'id'>;

export type CalendarItem = {
	id: string;
	kind: 'event' | 'todo';
	source_id: number;
	title: string;
	start: string;
	end: string;
	all_day: boolean;
	color: EventColor;
	recurring: boolean;
	done: boolean;
};
