<script lang="ts">
	import { ApiError } from '$lib/api';
	import { categories as categoriesApi, expenses } from '$lib/data';
	import { todayStr } from '$lib/dates';
	import { centsToInput, parseAmount } from '$lib/money';
	import type { Expense, ExpenseCategory, ExpenseInput } from '$lib/types';
	import Button from '$lib/ui/Button.svelte';
	import Select from '$lib/ui/Select.svelte';
	import TextField from '$lib/ui/TextField.svelte';
	import FormActions from './FormActions.svelte';

	let {
		expense,
		date,
		onsaved,
		oncancel
	}: {
		expense?: Expense;
		date?: string;
		onsaved: () => void;
		oncancel: () => void;
	} = $props();

	const PAYMENT_METHODS = ['Card', 'Cash', 'Bank transfer'];

	// Seeded once from the expense (or default date) the sheet was opened with.
	// svelte-ignore state_referenced_locally
	let amount = $state(expense ? centsToInput(expense.amount_cents) : '');
	// svelte-ignore state_referenced_locally
	let spentOn = $state(expense?.spent_on ?? date ?? todayStr());
	// svelte-ignore state_referenced_locally
	let categoryId = $state<number | 0>(expense?.category_id ?? 0);
	// svelte-ignore state_referenced_locally
	let description = $state(expense?.description ?? '');
	// svelte-ignore state_referenced_locally
	let paymentMethod = $state(expense?.payment_method ?? '');

	let categoryList = $state<ExpenseCategory[]>([]);
	let error = $state<string | null>(null);
	let busy = $state(false);

	const methodListId = $props.id();
	// 0 stands for "no category" in the select.
	const categoryOptions = $derived([
		{ value: 0, label: 'Uncategorized' },
		...categoryList.map((c) => ({ value: c.id, label: c.name }))
	]);

	$effect(() => {
		categoriesApi.list().then((list) => (categoryList = list), () => {});
	});

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		const cents = parseAmount(amount);
		if (cents === null) {
			error = 'Enter an amount, like 12.50.';
			return;
		}
		if (!spentOn) {
			error = 'Pick a date.';
			return;
		}
		const input: ExpenseInput = {
			amount_cents: cents,
			spent_on: spentOn,
			category_id: categoryId || null,
			description: description.trim(),
			payment_method: paymentMethod.trim() || null
		};
		busy = true;
		error = null;
		try {
			if (expense) await expenses.update(expense.id, input);
			else await expenses.create(input);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not save the expense.';
		} finally {
			busy = false;
		}
	}

	async function remove() {
		if (!expense || !confirm('Delete this expense?')) return;
		busy = true;
		try {
			await expenses.remove(expense.id);
			onsaved();
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not delete the expense.';
			busy = false;
		}
	}
</script>

<form onsubmit={submit} novalidate>
	<div class="row">
		<!-- svelte-ignore a11y_autofocus -->
		<TextField
			label="Amount"
			bind:value={amount}
			inputmode="decimal"
			placeholder="0.00"
			autocomplete="off"
			autofocus={!expense}
			required
		/>
		<TextField label="Date" type="date" bind:value={spentOn} required />
	</div>

	<Select label="Category" bind:value={categoryId} options={categoryOptions} />
	<TextField label="Description (optional)" bind:value={description} maxlength={200} placeholder="e.g. Weekly shop" />

	<TextField
		label="Paid with (optional)"
		bind:value={paymentMethod}
		list={methodListId}
		maxlength={30}
	/>
	<datalist id={methodListId}>
		{#each PAYMENT_METHODS as method (method)}<option value={method}></option>{/each}
	</datalist>

	{#if error}<p class="error-box" role="alert">{error}</p>{/if}

	<FormActions>
		{#if expense}
			<Button variant="danger" onclick={remove} disabled={busy}>Delete</Button>
		{/if}
		<span class="spacer"></span>
		<Button onclick={oncancel}>Cancel</Button>
		<Button type="submit" variant="primary" disabled={busy}>{expense ? 'Save' : 'Add expense'}</Button>
	</FormActions>
</form>

<style>
	form {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
		gap: 0.75rem;
	}

	.spacer {
		flex: 1;
	}
</style>
