<script lang="ts">
	let { value = $bindable<number | null>(null), placeholder = 'All' } = $props();
</script>

<div class="flex items-center gap-2">
	<label class="text-xs text-neutral-400 whitespace-nowrap">Limit</label>
	<input
		type="number"
		min="1"
		bind:value
		{placeholder}
		class="w-24 border border-neutral-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400 text-neutral-700"
	/>
</div>
