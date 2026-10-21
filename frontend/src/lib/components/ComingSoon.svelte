<script lang="ts">
	import type { Accent } from '$lib/modules';
	import EmptyState from '$lib/ui/EmptyState.svelte';
	import Window from '$lib/ui/Window.svelte';

	let { title, accent, milestone }: { title: string; accent: Accent; milestone: number } =
		$props();
</script>

<svelte:head><title>{title} · Life Planner</title></svelte:head>

<Window {title} {accent}>
	<EmptyState message="Disk not inserted yet" hint="This module arrives in milestone {milestone}." />
</Window>
