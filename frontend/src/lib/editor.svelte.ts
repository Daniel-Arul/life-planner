import { events, expenses, todos } from './data';
import type { Expense, PlannerEvent, Todo } from './types';

/** Prefill for a new event: dates as "YYYY-MM-DD", times as "HH:MM". */
export type EventDraft = {
	startDate: string;
	endDate?: string;
	startTime?: string;
	endTime?: string;
	allDay?: boolean;
};

export type EditorTarget =
	| { kind: 'chooser'; date: string; time?: string }
	| { kind: 'event'; event?: PlannerEvent; draft?: EventDraft }
	| { kind: 'todo'; todo?: Todo; dueDate?: string }
	| { kind: 'expense'; expense?: Expense; date?: string };

/**
 * One app-wide editor sheet, so the calendar, to-do list, dashboard and the
 * quick-add button all open the same forms. Pages watch `revision` to refetch
 * after anything is saved.
 */
class Editor {
	target = $state<EditorTarget | null>(null);
	revision = $state(0);

	open(target: EditorTarget) {
		this.target = target;
	}

	close() {
		this.target = null;
	}

	/** Call after any create/update/delete so open pages reload. */
	changed() {
		this.revision++;
	}

	async editEvent(id: number) {
		this.open({ kind: 'event', event: await events.get(id) });
	}

	async editTodo(id: number) {
		this.open({ kind: 'todo', todo: await todos.get(id) });
	}

	async editExpense(id: number) {
		this.open({ kind: 'expense', expense: await expenses.get(id) });
	}
}

export const editor = new Editor();
