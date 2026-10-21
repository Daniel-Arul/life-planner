import { appConfig } from './config.svelte';

/** Format integer cents in the configured currency, e.g. 1250 -> "$12.50". */
export function formatMoney(cents: number, { compact = false } = {}): string {
	return new Intl.NumberFormat(undefined, {
		style: 'currency',
		currency: appConfig.currency,
		// "$12.50" rather than "CA$12.50" on browsers whose locale isn't en-CA.
		currencyDisplay: 'narrowSymbol',
		...(compact ? { notation: 'compact', maximumFractionDigits: 1 } : {})
	}).format(cents / 100);
}

/**
 * Parse what someone typed into a money field into cents, or null if it isn't a
 * positive amount. Accepts "12", "12.5", "$1,234.50" and comma decimals ("12,50").
 */
export function parseAmount(input: string): number | null {
	let text = input.trim().replace(/[^\d.,]/g, '');
	if (/,\d{1,2}$/.test(text) && !text.includes('.')) {
		text = text.replace(',', '.'); // comma as the decimal separator
	} else {
		text = text.replace(/,/g, ''); // commas as thousands separators
	}
	const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(text);
	if (!match) return null;
	const cents = Number(match[1]) * 100 + Number((match[2] ?? '').padEnd(2, '0'));
	return cents > 0 && Number.isSafeInteger(cents) ? cents : null;
}

/** Cents as a plain editable number, e.g. 1250 -> "12.50". */
export function centsToInput(cents: number | null): string {
	return cents === null ? '' : (cents / 100).toFixed(2);
}
