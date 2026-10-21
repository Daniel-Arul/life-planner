import { appConfig } from './config.svelte';
import type { WorkoutEntry, WorkoutKind } from './types';

export const weightUnit = () => (appConfig.units === 'imperial' ? 'lb' : 'kg');
export const distanceUnit = () => (appConfig.units === 'imperial' ? 'mi' : 'km');

/** Trim trailing zeros: 60 -> "60", 72.5 -> "72.5", 5.25 -> "5.25". */
export function formatNumber(n: number): string {
	return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

/** Seconds as "28:00" or "1:05:30". */
export function formatDuration(seconds: number): string {
	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	const s = seconds % 60;
	const mm = h ? String(m).padStart(2, '0') : String(m);
	return `${h ? `${h}:` : ''}${mm}:${String(s).padStart(2, '0')}`;
}

/**
 * Parse a duration typed as "28:00", "1:05:30" or plain minutes ("45"), into
 * seconds. Returns null for blank input and undefined for garbage.
 */
export function parseDuration(text: string): number | null | undefined {
	const t = text.trim();
	if (!t) return null;
	if (/^\d+(\.\d+)?$/.test(t)) return Math.round(Number(t) * 60);
	const parts = t.split(':');
	if (parts.length > 3 || parts.some((p) => !/^\d+$/.test(p))) return undefined;
	return parts.reduce((total, part) => total * 60 + Number(part), 0);
}

/** One-line summary of an entry, e.g. "3 × 8 @ 60 kg" or "5.2 km · 28:00". */
export function summarizeEntry(entry: Omit<WorkoutEntry, 'id' | 'exercise_id' | 'exercise_name'>): string {
	const parts: string[] = [];
	if (entry.reps !== null) parts.push(`${entry.sets} × ${entry.reps}`);
	else if (entry.sets > 1) parts.push(`${entry.sets} sets`);
	if (entry.weight !== null) parts.push(`@ ${formatNumber(entry.weight)} ${weightUnit()}`);
	const cardio = [
		entry.distance !== null ? `${formatNumber(entry.distance)} ${distanceUnit()}` : null,
		entry.duration_s !== null ? formatDuration(entry.duration_s) : null
	].filter(Boolean);
	if (cardio.length) parts.push(cardio.join(' · '));
	return parts.join(' ');
}

export function kindLabel(kind: WorkoutKind): string {
	return kind.charAt(0).toUpperCase() + kind.slice(1);
}
