// Helpers for the backend's timezone-less local times. Everything here works in
// the browser's local time, which is the planner's wall-clock time.

const pad = (n: number) => String(n).padStart(2, '0');

/** "YYYY-MM-DD" for a local Date. */
export function toDateStr(d: Date): string {
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** "HH:MM" for a local Date. */
export function toTimeStr(d: Date): string {
	return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** "YYYY-MM-DDTHH:MM:00", the format the API expects. */
export function toLocalISO(d: Date): string {
	return `${toDateStr(d)}T${toTimeStr(d)}:00`;
}

/** Parse an API date or date-time as local time ("YYYY-MM-DD" alone would parse as UTC). */
export function parseLocal(s: string): Date {
	return new Date(s.length === 10 ? `${s}T00:00:00` : s);
}

export function addDays(d: Date, days: number): Date {
	const copy = new Date(d);
	copy.setDate(copy.getDate() + days);
	return copy;
}

/** "YYYY-MM" for a local Date. */
export function toMonthStr(d: Date): string {
	return toDateStr(d).slice(0, 7);
}

/** Shift a "YYYY-MM" month by n months. */
export function addMonths(month: string, n: number): string {
	const [year, mon] = month.split('-').map(Number);
	return toMonthStr(new Date(year, mon - 1 + n, 1));
}

/** "October 2026" for "2026-10". */
export function formatMonth(month: string, style: 'long' | 'short' = 'long'): string {
	const [year, mon] = month.split('-').map(Number);
	return new Date(year, mon - 1, 1).toLocaleDateString([], { month: style, year: 'numeric' });
}

export function todayStr(): string {
	return toDateStr(new Date());
}

/** Whole days from today to the given date (negative = past). */
export function daysFromToday(dateStr: string): number {
	const today = parseLocal(todayStr());
	return Math.round((parseLocal(dateStr).getTime() - today.getTime()) / 86_400_000);
}

/** Friendly due-date label: Today, Tomorrow, Yesterday, or "Wed 21 Oct". */
export function formatDay(dateStr: string): string {
	const diff = daysFromToday(dateStr);
	if (diff === 0) return 'Today';
	if (diff === 1) return 'Tomorrow';
	if (diff === -1) return 'Yesterday';
	return parseLocal(dateStr).toLocaleDateString([], {
		weekday: 'short',
		day: 'numeric',
		month: 'short'
	});
}

export function formatTime(d: Date): string {
	return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}
