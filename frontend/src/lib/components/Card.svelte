<script lang="ts">
	import type { Snippet } from 'svelte';
	let { class: cls = '', children } = $props<{ class?: string; children: Snippet }>();
</script>

<div class="border border-neutral-200 rounded-lg bg-white p-6 {cls}">
	{@render children()}
</div>
