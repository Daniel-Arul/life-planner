<script lang="ts">
	let { label = 'Loading' }: { label?: string } = $props();
</script>

<div class="wrap">
	<span class="label">{label}…</span>
	<div class="bar" role="progressbar" aria-label={label}>
		<div class="fill"></div>
	</div>
</div>

<style>
	.wrap {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.label {
		font-family: var(--font-pixel);
	}

	.bar {
		width: 12rem;
		height: 1.25rem;
		padding: 2px;
		border: 2px solid var(--color-ink);
		background: var(--color-surface);
	}

	.fill {
		height: 100%;
		/* Chunky blocks, like an old installer. */
		background: repeating-linear-gradient(
			to right,
			var(--color-lavender) 0 10px,
			transparent 10px 12px
		);
		animation: load 1.6s steps(12) infinite;
	}

	@keyframes load {
		from {
			width: 0;
		}
		to {
			width: 100%;
		}
	}
</style>
