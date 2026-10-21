import { api } from './api';
import { toLocalISO } from './dates';
import type {
	CalendarItem,
	EventInput,
	Expense,
	ExpenseCategory,
	ExpenseInput,
	ExpenseStats,
	PlannerEvent,
	Todo,
	TodoInput
} from './types';

export const todos = {
	list: (status: 'open' | 'done' | 'all' = 'open', tag?: string) => {
		const params = new URLSearchParams({ status });
		if (tag) params.set('tag', tag);
		return api.get<Todo[]>(`/todos?${params}`);
	},
	tags: () => api.get<string[]>('/todos/tags'),
	get: (id: number) => api.get<Todo>(`/todos/${id}`),
	create: (input: TodoInput) => api.post<Todo>('/todos', input),
	update: (id: number, changes: Partial<TodoInput>) => api.patch<Todo>(`/todos/${id}`, changes),
	remove: (id: number) => api.delete(`/todos/${id}`),
	reorder: (ids: number[]) => api.put<void>('/todos/reorder', { ids })
};

export const events = {
	get: (id: number) => api.get<PlannerEvent>(`/events/${id}`),
	create: (input: EventInput) => api.post<PlannerEvent>('/events', input),
	update: (id: number, changes: Partial<EventInput>) =>
		api.patch<PlannerEvent>(`/events/${id}`, changes),
	remove: (id: number) => api.delete(`/events/${id}`)
};

export const expenses = {
	list: (month: string) => api.get<Expense[]>(`/expenses?month=${month}`),
	get: (id: number) => api.get<Expense>(`/expenses/${id}`),
	create: (input: ExpenseInput) => api.post<Expense>('/expenses', input),
	update: (id: number, changes: Partial<ExpenseInput>) =>
		api.patch<Expense>(`/expenses/${id}`, changes),
	remove: (id: number) => api.delete(`/expenses/${id}`),
	stats: (month: string) => api.get<ExpenseStats>(`/stats/expenses?month=${month}`)
};

export const categories = {
	list: () => api.get<ExpenseCategory[]>('/expense-categories'),
	create: (name: string, monthly_budget_cents: number | null) =>
		api.post<ExpenseCategory>('/expense-categories', { name, monthly_budget_cents }),
	update: (id: number, changes: Partial<Pick<ExpenseCategory, 'name' | 'monthly_budget_cents'>>) =>
		api.patch<ExpenseCategory>(`/expense-categories/${id}`, changes),
	remove: (id: number) => api.delete(`/expense-categories/${id}`)
};

export function fetchCalendar(start: Date, end: Date) {
	const params = new URLSearchParams({ start: toLocalISO(start), end: toLocalISO(end) });
	return api.get<CalendarItem[]>(`/calendar?${params}`);
}
