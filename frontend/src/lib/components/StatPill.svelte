<script lang="ts">
	let { label, value } = $props<{ label: string; value: string | number }>();
</script>

<div class="inline-flex flex-col items-center px-4 py-2 bg-neutral-50 border border-neutral-200 rounded-lg">
	<span class="text-2xl font-semibold text-neutral-900">{value}</span>
	<span class="text-xs text-neutral-400 mt-0.5">{label}</span>
</div>
