<script lang="ts">
	let { value, max, label = '' } = $props<{ value: number; max: number; label?: string }>();
	const pct = $derived(max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0);
</script>

<div class="w-full">
	{#if label}
		<div class="flex justify-between text-xs text-neutral-400 mb-1">
			<span>{label}</span>
			<span>{value} / {max}</span>
		</div>
	{/if}
	<div class="h-px bg-neutral-100 rounded-full overflow-hidden">
		<div
			class="h-full bg-neutral-900 transition-all duration-500"
			style="width: {pct}%"
		></div>
	</div>
</div>
