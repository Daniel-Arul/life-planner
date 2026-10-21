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
	kind: 'event' | 'todo' | 'expense';
	source_id: number;
	title: string;
	start: string;
	end: string;
	all_day: boolean;
	color: EventColor;
	recurring: boolean;
	done: boolean;
	/** Daily total, for kind 'expense'. */
	amount_cents: number | null;
};

// Money is integer cents throughout.
export type ExpenseCategory = {
	id: number;
	name: string;
	monthly_budget_cents: number | null;
	position: number;
};

export type Expense = {
	id: number;
	spent_on: string;
	amount_cents: number;
	category_id: number | null;
	description: string;
	payment_method: string | null;
};

export type ExpenseInput = Omit<Expense, 'id'>;

export type ExpenseStats = {
	month: string;
	total_cents: number;
	previous_total_cents: number;
	budget_cents: number | null;
	categories: { id: number | null; name: string; total_cents: number; budget_cents: number | null }[];
	daily: { date: string; total_cents: number }[];
};
