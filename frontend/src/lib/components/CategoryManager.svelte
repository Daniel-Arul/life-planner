<script lang="ts">
	import { ApiError } from '$lib/api';
	import { categories as categoriesApi } from '$lib/data';
	import { editor } from '$lib/editor.svelte';
	import { centsToInput, formatMoney, parseAmount } from '$lib/money';
	import type { ExpenseCategory } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';

	let list = $state<ExpenseCategory[]>([]);
	let error = $state<string | null>(null);
	let saved = $state<number | null>(null);
	let newName = $state('');
	let newBudget = $state('');

	$effect(() => {
		void editor.revision;
		categoriesApi.list().then((l) => (list = l), (err) => (error = message(err)));
	});

	function message(err: unknown) {
		return err instanceof ApiError ? err.message : 'Something went wrong.';
	}

	/** Blank means "no budget"; anything else must parse as money. */
	function budgetFrom(text: string): number | null | undefined {
		if (!text.trim()) return null;
		return parseAmount(text) ?? undefined;
	}

	async function update(category: ExpenseCategory, field: 'name' | 'budget', value: string) {
		const changes =
			field === 'name' ? { name: value.trim() } : { monthly_budget_cents: budgetFrom(value) };
		if (field === 'name' && !changes.name) return (error = 'Category names cannot be empty.');
		if ('monthly_budget_cents' in changes && changes.monthly_budget_cents === undefined)
			return (error = `"${value}" isn't an amount.`);
		try {
			await categoriesApi.update(category.id, changes);
			error = null;
			saved = category.id;
			setTimeout(() => (saved = null), 1200);
			editor.changed();
		} catch (err) {
			error = message(err);
		}
	}

	async function remove(category: ExpenseCategory) {
		if (!confirm(`Delete "${category.name}"? Its expenses become uncategorized.`)) return;
		try {
			await categoriesApi.remove(category.id);
			editor.changed();
		} catch (err) {
			error = message(err);
		}
	}

	async function add(e: SubmitEvent) {
		e.preventDefault();
		const budget = budgetFrom(newBudget);
		if (!newName.trim()) return;
		if (budget === undefined) return (error = `"${newBudget}" isn't an amount.`);
		try {
			await categoriesApi.create(newName.trim(), budget);
			newName = '';
			newBudget = '';
			error = null;
			editor.changed();
		} catch (err) {
			error = message(err);
		}
	}
</script>

<p class="intro">Changes save when you leave a field. Leave a budget blank for no limit.</p>

{#if error}<p class="error-box" role="alert">{error}</p>{/if}

<table>
	<thead>
		<tr>
			<th scope="col">Category</th>
			<th scope="col">Monthly budget</th>
			<th scope="col"><span class="sr-only">Actions</span></th>
		</tr>
	</thead>
	<tbody>
		{#each list as category (category.id)}
			<tr>
				<td>
					<input
						class="retro-input"
						aria-label="Name"
						value={category.name}
						maxlength={40}
						onchange={(e) => update(category, 'name', e.currentTarget.value)}
					/>
				</td>
				<td class="budget">
					<input
						class="retro-input tabular"
						aria-label="{category.name} monthly budget"
						inputmode="decimal"
						placeholder="None"
						value={centsToInput(category.monthly_budget_cents)}
						onchange={(e) => update(category, 'budget', e.currentTarget.value)}
					/>
				</td>
				<td class="actions">
					{#if saved === category.id}<span class="saved" role="status">Saved</span>{/if}
					<button type="button" class="delete" aria-label="Delete {category.name}" onclick={() => remove(category)}>×</button>
				</td>
			</tr>
		{/each}
	</tbody>
</table>

<form class="add" onsubmit={add}>
	<input class="retro-input" aria-label="New category name" placeholder="New category" maxlength={40} bind:value={newName} />
	<input class="retro-input tabular" aria-label="New category budget" placeholder="Budget" inputmode="decimal" bind:value={newBudget} />
	<Button type="submit">Add</Button>
</form>

{#if list.some((c) => c.monthly_budget_cents)}
	<p class="total">
		Total monthly budget:
		<strong class="tabular">{formatMoney(list.reduce((sum, c) => sum + (c.monthly_budget_cents ?? 0), 0))}</strong>
	</p>
{/if}

<style>
	.intro {
		margin: 0 0 1rem;
		font-size: 0.85rem;
		color: var(--color-muted);
	}

	.error-box {
		margin-bottom: 1rem;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		table-layout: fixed;
	}

	th:nth-child(2),
	.budget {
		width: 6.5rem;
	}

	th:nth-child(3) {
		width: 3.5rem;
	}

	td .retro-input {
		padding-inline: 0.5rem;
	}

	th {
		padding: 0 0.25rem 0.4rem;
		font-family: var(--font-pixel);
		font-weight: 400;
		font-size: 0.85rem;
		text-align: left;
	}

	td {
		padding: 0.25rem;
	}

	.actions {
		position: relative;
		text-align: right;
	}

	.saved {
		position: absolute;
		right: calc(100% + 0.25rem);
		top: 50%;
		transform: translateY(-50%);
		padding: 0 0.3rem;
		font-size: 0.75rem;
		background: var(--color-butter);
		border: 2px solid var(--color-ink);
	}

	.delete {
		width: 44px;
		height: 44px;
		font-size: 1.2rem;
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		cursor: pointer;
	}

	.delete:hover {
		background: var(--color-rose);
	}

	.add {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.add :global(.btn) {
		grid-column: 1 / -1;
	}

	@media (min-width: 640px) {
		.add {
			grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) auto;
		}

		.add :global(.btn) {
			grid-column: auto;
		}
	}

	.total {
		margin: 1rem 0 0;
	}
</style>
