// Repeat presets for the event form, stored as RRULE bodies. 'none' means no rrule.
export const REPEATS: { value: string; label: string }[] = [
	{ value: 'none', label: 'Does not repeat' },
	{ value: 'FREQ=DAILY', label: 'Every day' },
	{ value: 'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR', label: 'Every weekday (Mon–Fri)' },
	{ value: 'FREQ=WEEKLY', label: 'Every week' },
	{ value: 'FREQ=WEEKLY;INTERVAL=2', label: 'Every 2 weeks' },
	{ value: 'FREQ=MONTHLY', label: 'Every month' },
	{ value: 'FREQ=YEARLY', label: 'Every year' }
];

/** Separate an rrule's UNTIL (as "YYYY-MM-DD") from the rest, so presets can match. */
export function splitRrule(rrule: string | null): { rule: string; until: string } {
	if (!rrule) return { rule: 'none', until: '' };
	let until = '';
	const parts = rrule.split(';').filter((part) => {
		const match = /^UNTIL=(\d{4})(\d{2})(\d{2})/.exec(part);
		if (match) until = `${match[1]}-${match[2]}-${match[3]}`;
		return !match;
	});
	return { rule: parts.join(';'), until };
}

/** Rebuild the rrule; UNTIL covers the whole last day. */
export function buildRrule(rule: string, until: string): string | null {
	if (rule === 'none') return null;
	return until ? `${rule};UNTIL=${until.replaceAll('-', '')}T235959` : rule;
}
