<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	let {
		variant = 'default',
		type = 'button',
		class: className = '',
		children,
		...rest
	}: HTMLButtonAttributes & {
		variant?: 'default' | 'primary' | 'danger';
		children: Snippet;
	} = $props();
</script>

<button {type} class="btn {variant} {className}" {...rest}>
	{@render children()}
</button>

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		min-height: 44px;
		padding: 0.5rem 1rem;
		font-family: var(--font-pixel);
		font-size: 1rem;
		color: var(--color-ink);
		background: var(--color-surface);
		border: 2px solid var(--color-ink);
		border-radius: 0;
		/* Bevel highlight + shade, then the hard drop shadow. */
		box-shadow:
			inset 2px 2px 0 rgb(255 255 255 / 0.8),
			inset -2px -2px 0 color-mix(in srgb, var(--color-ink) 15%, transparent),
			var(--shadow-hard-sm);
		cursor: pointer;
		user-select: none;
		transition: transform 60ms steps(1);
	}

	.primary {
		background: var(--color-lavender);
	}

	.danger {
		background: var(--color-rose);
	}

	.btn:active:not(:disabled) {
		transform: translate(2px, 2px);
		box-shadow:
			inset 2px 2px 0 color-mix(in srgb, var(--color-ink) 15%, transparent),
			inset -2px -2px 0 rgb(255 255 255 / 0.6);
	}

	.btn:disabled {
		cursor: not-allowed;
		color: var(--color-muted);
		background-image: repeating-linear-gradient(
			45deg,
			transparent 0 3px,
			color-mix(in srgb, var(--color-ink) 8%, transparent) 3px 4px
		);
	}
</style>
