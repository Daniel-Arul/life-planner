<script lang="ts">
	import Pixel from './Pixel.svelte';
	import { floppy } from './icons';

	let { message, hint }: { message: string; hint?: string } = $props();
</script>

<div class="empty">
	<Pixel art={floppy} size={40} />
	<p class="message">{message}</p>
	{#if hint}<p class="hint">{hint}</p>{/if}
</div>

<style>
	.empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		padding: 1rem 0;
		text-align: center;
	}

	p {
		margin: 0;
	}

	.message {
		margin-top: 0.5rem;
		font-family: var(--font-pixel);
	}

	.hint {
		font-size: 0.85rem;
		color: var(--color-muted);
	}
</style>
