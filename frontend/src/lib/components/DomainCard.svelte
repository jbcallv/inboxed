<script lang="ts">
	import ProgressLine from './ProgressLine.svelte';
	import { post } from '$lib/api';

	let { domain, onStatusChange } = $props<{
		domain: {
			id: string;
			domain: string;
			from_name: string;
			status: string;
			sent_today: number;
			cap_today: number;
			warmup_started_on: string;
		};
		onStatusChange?: () => void;
	}>();

	let loading = $state(false);

	async function toggle() {
		loading = true;
		const action = domain.status === 'paused' ? 'resume' : 'pause';
		await post(`/api/domains/${domain.id}/${action}`).catch(() => {});
		onStatusChange?.();
		loading = false;
	}
</script>

<div class="border border-neutral-200 rounded-lg bg-white p-4">
	<div class="flex items-start justify-between mb-3">
		<div>
			<p class="font-medium text-sm text-neutral-900">{domain.domain}</p>
			<p class="text-xs text-neutral-400 mt-0.5">{domain.from_name}</p>
		</div>
		<div class="flex items-center gap-2">
			<span class="text-xs px-2 py-0.5 rounded-full border
				{domain.status === 'active' ? 'border-green-200 text-green-700 bg-green-50' :
				 domain.status === 'paused' ? 'border-red-200 text-red-700 bg-red-50' :
				 'border-yellow-200 text-yellow-700 bg-yellow-50'}">
				{domain.status}
			</span>
			<button
				onclick={toggle}
				disabled={loading}
				class="text-xs px-2 py-0.5 rounded border border-neutral-200 text-neutral-500 hover:bg-neutral-50 disabled:opacity-40 transition-colors">
				{domain.status === 'paused' ? 'Resume' : 'Pause'}
			</button>
		</div>
	</div>
	<ProgressLine value={domain.sent_today} max={domain.cap_today} label="today" />
</div>
