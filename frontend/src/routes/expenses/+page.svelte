<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { tick } from 'svelte';
	import { ApiError } from '$lib/api';
	import { categories as categoriesApi, expenses as expensesApi } from '$lib/data';
	import { addMonths, formatDay, formatMonth, parseLocal, toMonthStr, todayStr } from '$lib/dates';
	import { editor } from '$lib/editor.svelte';
	import { formatMoney, parseAmount } from '$lib/money';
	import type { Expense, ExpenseCategory, ExpenseStats } from '$lib/types';
	import BudgetMeter from '$lib/ui/BudgetMeter.svelte';
	import Button from '$lib/ui/Button.svelte';
	import ColumnChart from '$lib/ui/ColumnChart.svelte';
	import EmptyState from '$lib/ui/EmptyState.svelte';
	import ProgressBar from '$lib/ui/ProgressBar.svelte';
	import Window from '$lib/ui/Window.svelte';

	const thisMonth = toMonthStr(new Date());
	const fromUrl = page.url.searchParams.get('month');
	let month = $state(fromUrl && /^\d{4}-\d{2}$/.test(fromUrl) ? fromUrl : thisMonth);
	// A day to scroll to once loaded (calendar links here with ?day=).
	let focusDay = page.url.searchParams.get('day');

	let stats = $state<ExpenseStats | null>(null);
	let list = $state<Expense[]>([]);
	let categoryList = $state<ExpenseCategory[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let highlighted = $state<string | null>(null);

	// Quick add.
	let amount = $state('');
	let categoryId = $state(0);
	let description = $state('');
	let adding = $state(false);

	const categoryNames = $derived(new Map(categoryList.map((c) => [c.id, c.name])));
	const byDay = $derived.by(() => {
		const groups: { date: string; total: number; items: Expense[] }[] = [];
		for (const expense of list) {
			const last = groups.at(-1);
			if (last?.date === expense.spent_on) {
				last.items.push(expense);
				last.total += expense.amount_cents;
			} else {
				groups.push({ date: expense.spent_on, total: expense.amount_cents, items: [expense] });
			}
		}
		return groups;
	});
	const delta = $derived(stats ? stats.total_cents - stats.previous_total_cents : 0);
	const previousName = $derived(formatMonth(addMonths(month, -1)).split(' ')[0]);

	let latest = 0;
	$effect(() => {
		void editor.revision;
		load(month);
	});

	async function load(forMonth: string) {
		const request = ++latest;
		loading = true;
		try {
			const [s, l, c] = await Promise.all([
				expensesApi.stats(forMonth),
				expensesApi.list(forMonth),
				categoriesApi.list()
			]);
			if (request !== latest) return;
			stats = s;
			list = l;
			categoryList = c;
			error = null;
			if (focusDay) {
				const day = focusDay;
				focusDay = null;
				await tick();
				showDay(day);
			}
		} catch (err) {
			if (request === latest) error = err instanceof ApiError ? err.message : 'Could not load expenses.';
		} finally {
			if (request === latest) loading = false;
		}
	}

	function changeMonth(next: string) {
		month = next;
		goto(`?month=${next}`, { replaceState: true, noScroll: true, keepFocus: true });
	}

	function showDay(date: string) {
		const el = document.getElementById(`day-${date}`);
		if (!el) return;
		el.scrollIntoView({ behavior: 'smooth', block: 'start' });
		highlighted = date;
		setTimeout(() => (highlighted = null), 1600);
	}

	async function quickAdd(e: SubmitEvent) {
		e.preventDefault();
		const cents = parseAmount(amount);
		if (cents === null) {
			error = 'Enter an amount, like 12.50.';
			return;
		}
		adding = true;
		try {
			await expensesApi.create({
				amount_cents: cents,
				// Today when looking at this month, otherwise the 1st of the month shown.
				spent_on: month === thisMonth ? todayStr() : `${month}-01`,
				category_id: categoryId || null,
				description: description.trim(),
				payment_method: null
			});
			amount = '';
			description = '';
			error = null;
			editor.changed();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not add the expense.';
		} finally {
			adding = false;
		}
	}
</script>

<svelte:head><title>Expenses · Life Planner</title></svelte:head>

<div class="page">
	<nav class="month-nav" aria-label="Month">
		<button type="button" class="nav-btn" aria-label="Previous month" onclick={() => changeMonth(addMonths(month, -1))}>‹</button>
		<h1>{formatMonth(month)}</h1>
		<button type="button" class="nav-btn" aria-label="Next month" onclick={() => changeMonth(addMonths(month, 1))}>›</button>
		{#if month !== thisMonth}
			<Button onclick={() => changeMonth(thisMonth)}>This month</Button>
		{/if}
	</nav>

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<div class="layout">
		<div class="summary">
			<Window title="Summary" accent="peach">
				{#if !stats}
					<ProgressBar label="Counting" />
				{:else}
					<div class="hero">
						<span class="label">Spent in {formatMonth(month, 'long').split(' ')[0]}</span>
						<span class="value">{formatMoney(stats.total_cents)}</span>
						<span class="delta" class:up={delta > 0}>
							{#if stats.previous_total_cents === 0}
								Nothing logged in {previousName}
							{:else if delta === 0}
								Same as {previousName}
							{:else}
								<span aria-hidden="true">{delta > 0 ? '▲' : '▼'}</span>
								{formatMoney(Math.abs(delta))} {delta > 0 ? 'more' : 'less'} than {previousName}
							{/if}
						</span>
					</div>
					{#if stats.budget_cents}
						<BudgetMeter spent={stats.total_cents} budget={stats.budget_cents} label="Monthly budget" />
					{/if}
					<h3 class="chart-title">Per day</h3>
					<ColumnChart
						columns={stats.daily.map((d) => ({
							key: d.date,
							value: d.total_cents,
							label: formatDay(d.date),
							tick: String(parseLocal(d.date).getDate())
						}))}
						formatValue={(v) => formatMoney(v)}
						formatTick={(v) => formatMoney(v, { compact: true })}
						label="Spending per day"
						{loading}
						onselect={showDay}
					/>
				{/if}
			</Window>
		</div>

		<div class="cats">
			<Window title="Categories" accent="peach">
				{#if stats && stats.categories.length}
					<ul class="cat-list">
						{#each stats.categories as cat (cat.id ?? 'none')}
							<li>
								<div class="cat-head">
									<span class="cat-name">{cat.name}</span>
									<span class="cat-amount tabular">
										{formatMoney(cat.total_cents)}
										{#if stats.total_cents > 0}
											<span class="share">{Math.round((cat.total_cents / stats.total_cents) * 100)}%</span>
										{/if}
									</span>
								</div>
								{#if cat.budget_cents}
									<BudgetMeter spent={cat.total_cents} budget={cat.budget_cents} label="{cat.name} budget" />
								{/if}
							</li>
						{/each}
					</ul>
				{:else if stats}
					<EmptyState message="No spending yet" />
				{/if}
				<p class="manage"><a href="/settings">Edit categories &amp; budgets →</a></p>
			</Window>
		</div>

		<div class="list">
			<Window title="Expenses" accent="peach">
				<form class="quick-add" onsubmit={quickAdd}>
					<input
						class="retro-input amount"
						aria-label="Amount"
						placeholder="0.00"
						inputmode="decimal"
						autocomplete="off"
						bind:value={amount}
					/>
					<select class="retro-input" aria-label="Category" bind:value={categoryId}>
						<option value={0}>Uncategorized</option>
						{#each categoryList as c (c.id)}<option value={c.id}>{c.name}</option>{/each}
					</select>
					<input
						class="retro-input desc"
						aria-label="Description"
						placeholder="What for? (optional)"
						maxlength={200}
						bind:value={description}
					/>
					<Button type="submit" variant="primary" disabled={adding}>Add</Button>
				</form>
				<p class="hint">
					Quick add logs it {month === thisMonth ? 'today' : `on the 1st of ${formatMonth(month)}`}.
					<button type="button" class="link" onclick={() => editor.open({ kind: 'expense', date: month === thisMonth ? todayStr() : `${month}-01` })}>
						Pick a date…
					</button>
				</p>

				{#if !loading && list.length === 0}
					<EmptyState message="No expenses this month" hint="Add one above." />
				{:else}
					<div class="days" class:loading>
						{#each byDay as group (group.date)}
							<section id="day-{group.date}" class="day" class:highlighted={highlighted === group.date}>
								<h3 class="day-head">
									<span>{formatDay(group.date)}</span>
									<span class="tabular">{formatMoney(group.total)}</span>
								</h3>
								<ul>
									{#each group.items as expense (expense.id)}
										<li>
											<button type="button" class="row" onclick={() => editor.open({ kind: 'expense', expense })}>
												<span class="what">
													<span class="desc-text">
														{expense.description || categoryNames.get(expense.category_id ?? -1) || 'Expense'}
													</span>
													{#if expense.category_id && expense.description}
														<span class="badge">{categoryNames.get(expense.category_id)}</span>
													{/if}
												</span>
												<span class="amount-text tabular">{formatMoney(expense.amount_cents)}</span>
											</button>
										</li>
									{/each}
								</ul>
							</section>
						{/each}
					</div>
				{/if}
			</Window>
		</div>
	</div>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.month-nav {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.month-nav h1 {
		margin: 0;
		min-width: 10ch;
		font-size: 1.5rem;
		text-align: center;
	}

	.nav-btn {
		width: 44px;
		height: 44px;
		font-family: var(--font-pixel);
		font-size: 1.4rem;
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		box-shadow: var(--shadow-hard-sm);
		cursor: pointer;
	}

	.nav-btn:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}

	.layout {
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		grid-template-areas: 'summary' 'list' 'cats';
		gap: 1rem;
	}

	.summary {
		grid-area: summary;
	}

	.cats {
		grid-area: cats;
	}

	.list {
		grid-area: list;
	}

	@media (min-width: 1024px) {
		.layout {
			grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
			grid-template-areas: 'summary list' 'cats list';
			grid-template-rows: auto 1fr;
			gap: 1.5rem;
			align-items: start;
		}
	}

	/* Hero figure: the one number this page leads with. */
	.hero {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		margin-bottom: 1rem;
	}

	.hero .label {
		font-family: var(--font-pixel);
		color: var(--color-muted);
	}

	.hero .value {
		font-size: 3rem;
		font-weight: 600;
		line-height: 1.1;
		overflow-wrap: anywhere;
	}

	.delta {
		font-size: 0.9rem;
		color: var(--color-muted);
	}

	.delta.up {
		color: var(--color-alert);
	}

	.chart-title {
		margin: 1.25rem 0 0.5rem;
		font-size: 0.95rem;
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.cat-list {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
	}

	.cat-head {
		display: flex;
		justify-content: space-between;
		gap: 0.5rem;
		margin-bottom: 0.3rem;
	}

	.cat-name {
		font-family: var(--font-pixel);
	}

	.share {
		margin-left: 0.4rem;
		font-size: 0.8rem;
		color: var(--color-muted);
	}

	.manage {
		margin: 1rem 0 0;
		font-size: 0.85rem;
	}

	.manage a,
	.link {
		font: inherit;
		color: var(--color-ink);
		background: none;
		border: 0;
		padding: 0;
		text-decoration: underline;
		cursor: pointer;
	}

	.quick-add {
		display: grid;
		grid-template-columns: 7rem minmax(0, 1fr);
		gap: 0.5rem;
	}

	.quick-add .desc {
		grid-column: 1 / -1;
	}

	.quick-add :global(.btn) {
		grid-column: 1 / -1;
	}

	@media (min-width: 640px) {
		.quick-add {
			grid-template-columns: 7rem minmax(0, 10rem) minmax(0, 1fr) auto;
		}

		.quick-add .desc,
		.quick-add :global(.btn) {
			grid-column: auto;
		}
	}

	.hint {
		margin: 0.5rem 0 1rem;
		font-size: 0.8rem;
		color: var(--color-muted);
	}

	.days {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		transition: opacity 150ms;
	}

	.days.loading {
		opacity: 0.5;
	}

	.day {
		scroll-margin-top: 4rem;
		border: 2px solid var(--color-ink);
		transition: box-shadow 150ms;
	}

	.day.highlighted {
		box-shadow: 0 0 0 4px var(--color-peach);
	}

	.day-head {
		display: flex;
		justify-content: space-between;
		margin: 0;
		padding: 0.3rem 0.6rem;
		font-size: 0.9rem;
		background: color-mix(in srgb, var(--color-peach) 40%, var(--color-surface));
		border-bottom: 2px solid var(--color-ink);
	}

	.day-head .tabular {
		font-weight: 600;
	}

	.day li + li {
		border-top: 2px dotted var(--color-grid);
	}

	.row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		width: 100%;
		min-height: 44px;
		padding: 0.35rem 0.6rem;
		font: inherit;
		color: inherit;
		text-align: left;
		background: var(--color-surface);
		border: 0;
		cursor: pointer;
	}

	.what {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.25rem 0.5rem;
		min-width: 0;
	}

	.desc-text {
		overflow-wrap: anywhere;
	}

	.amount-text {
		flex-shrink: 0;
		font-weight: 600;
	}

	@media (hover: hover) {
		.row:hover {
			background: color-mix(in srgb, var(--color-peach) 20%, var(--color-surface));
		}
	}
</style>
