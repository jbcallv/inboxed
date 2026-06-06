<script lang="ts">
	import ProgressLine from './ProgressLine.svelte';

	let { domain } = $props<{
		domain: {
			id: string;
			domain: string;
			from_name: string;
			status: string;
			sent_today: number;
			cap_today: number;
			warmup_started_on: string;
		};
	}>();
</script>

<div class="border border-neutral-200 rounded-lg bg-white p-4">
	<div class="flex items-start justify-between mb-3">
		<div>
			<p class="font-medium text-sm text-neutral-900">{domain.domain}</p>
			<p class="text-xs text-neutral-400 mt-0.5">{domain.from_name}</p>
		</div>
		<span class="text-xs px-2 py-0.5 rounded-full border
			{domain.status === 'active' ? 'border-green-200 text-green-700 bg-green-50' :
			 domain.status === 'paused' ? 'border-red-200 text-red-700 bg-red-50' :
			 'border-yellow-200 text-yellow-700 bg-yellow-50'}">
			{domain.status}
		</span>
	</div>
	<ProgressLine value={domain.sent_today} max={domain.cap_today} label="today" />
</div>
