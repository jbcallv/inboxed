<script lang="ts">
	let { step, title, description = '' } = $props<{
		step: number;
		title: string;
		description?: string;
	}>();
</script>

<div class="mb-6">
	<p class="text-xs font-medium tracking-widest text-neutral-400 uppercase mb-1">Step {step}</p>
	<h2 class="text-xl font-semibold text-neutral-900">{title}</h2>
	{#if description}
		<p class="mt-1 text-sm text-neutral-500">{description}</p>
	{/if}
</div>
<hr class="border-neutral-100 mb-6" />
