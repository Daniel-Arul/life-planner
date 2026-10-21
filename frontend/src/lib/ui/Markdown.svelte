<script lang="ts">
	import { renderMarkdown } from '$lib/markdown';

	let { source }: { source: string } = $props();

	const html = $derived(renderMarkdown(source));
</script>

<!-- Sanitized by DOMPurify in renderMarkdown. -->
<div class="prose">{@html html}</div>

<style>
	.prose {
		line-height: 1.55;
		overflow-wrap: anywhere;
	}

	.prose :global(:first-child) {
		margin-top: 0;
	}

	.prose :global(:last-child) {
		margin-bottom: 0;
	}

	.prose :global(h1),
	.prose :global(h2),
	.prose :global(h3) {
		margin: 1.1em 0 0.4em;
		line-height: 1.25;
	}

	.prose :global(h1) {
		font-size: 1.35rem;
	}

	.prose :global(h2) {
		font-size: 1.15rem;
	}

	.prose :global(h3) {
		font-size: 1rem;
	}

	.prose :global(p),
	.prose :global(ul),
	.prose :global(ol),
	.prose :global(pre),
	.prose :global(blockquote) {
		margin: 0.6em 0;
	}

	.prose :global(ul),
	.prose :global(ol) {
		padding-left: 1.4em;
	}

	/* Square pixel bullets. */
	.prose :global(ul) {
		list-style: square;
	}

	.prose :global(li:has(> input[type='checkbox'])) {
		list-style: none;
		margin-left: -1.4em;
	}

	.prose :global(input[type='checkbox']) {
		margin-right: 0.4em;
		accent-color: var(--color-ink);
	}

	.prose :global(a) {
		color: var(--color-ink);
		text-decoration-thickness: 2px;
		text-decoration-color: var(--color-sky);
	}

	.prose :global(code) {
		padding: 0 0.25em;
		font-size: 0.9em;
		background: color-mix(in srgb, var(--color-sky) 35%, var(--color-surface));
		border: 1px solid color-mix(in srgb, var(--color-ink) 25%, transparent);
	}

	.prose :global(pre) {
		padding: 0.6em 0.8em;
		overflow-x: auto;
		background: var(--color-ink);
		color: var(--color-surface);
	}

	.prose :global(pre code) {
		padding: 0;
		background: none;
		border: 0;
	}

	.prose :global(blockquote) {
		padding-left: 0.8em;
		border-left: 4px solid var(--color-sky);
		color: var(--color-muted);
	}

	.prose :global(hr) {
		border: 0;
		border-top: 2px dashed var(--color-grid);
	}

	.prose :global(img) {
		max-width: 100%;
	}

	.prose :global(table) {
		border-collapse: collapse;
	}

	.prose :global(th),
	.prose :global(td) {
		padding: 0.2em 0.6em;
		border: 1px solid color-mix(in srgb, var(--color-ink) 30%, transparent);
	}
</style>
