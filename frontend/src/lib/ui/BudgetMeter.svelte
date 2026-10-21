<script lang="ts">
	import { formatMoney } from '$lib/money';

	let {
		spent,
		budget,
		label
	}: {
		spent: number;
		budget: number;
		/** Accessible name, e.g. "Groceries budget". */
		label: string;
	} = $props();

	const over = $derived(spent > budget);
	const ratio = $derived(budget > 0 ? Math.min(spent / budget, 1) : 1);
</script>

<div class="meter-wrap">
	<div
		class="meter"
		role="meter"
		aria-label={label}
		aria-valuemin={0}
		aria-valuemax={budget}
		aria-valuenow={Math.min(spent, budget)}
		aria-valuetext="{formatMoney(spent)} of {formatMoney(budget)}"
	>
		<div class="fill" class:over style:width="{ratio * 100}%"></div>
	</div>
	<p class="caption tabular">
		{#if over}
			<!-- Status is never color alone: icon + words. -->
			<span class="over-label"><span class="icon" aria-hidden="true">!</span> Over by {formatMoney(spent - budget)}</span>
		{:else}
			{formatMoney(budget - spent)} left of {formatMoney(budget)}
		{/if}
	</p>
</div>

<style>
	.meter {
		height: 12px;
		padding: 2px;
		border: 2px solid var(--color-ink);
		/* Track: a lighter step of the same peach ramp as the fill. */
		background: var(--color-peach);
	}

	.fill {
		height: 100%;
		background: var(--color-peach-deep);
	}

	.fill.over {
		background: var(--color-alert);
	}

	.caption {
		margin: 0.3rem 0 0;
		font-size: 0.8rem;
		color: var(--color-muted);
	}

	.over-label {
		color: var(--color-alert);
		font-weight: 600;
	}

	.icon {
		display: inline-grid;
		place-items: center;
		width: 1rem;
		height: 1rem;
		font-size: 0.75rem;
		color: var(--color-surface);
		background: var(--color-alert);
	}
</style>
