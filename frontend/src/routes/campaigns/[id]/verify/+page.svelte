<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getToken } from '$lib/supabase';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import ProgressLine from '$lib/components/ProgressLine.svelte';

	const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
	const id = $derived($page.params.id);

	let running = $state(false);
	let done = $state(0);
	let total = $state(0);
	let kept = $state(0);
	let dropped = $state(0);
	let finished = $state(false);
	let warning = $state('');
	let error = $state('');

	async function startPrep() {
		running = true;
		error = '';
		warning = '';
		const token = await getToken();
		let res: Response;
		try {
			res = await fetch(`${BASE}/api/campaigns/${id}/prep`, {
				method: 'POST',
				headers: token ? { Authorization: `Bearer ${token}` } : {}
			});
		} catch (e: any) {
			error = `Could not reach API: ${e.message}`;
			running = false;
			return;
		}

		const reader = res.body!.getReader();
		const decoder = new TextDecoder();

		while (true) {
			const { value, done: streamDone } = await reader.read();
			if (streamDone) break;
			for (const line of decoder.decode(value).split('\n')) {
				if (!line.startsWith('data:')) continue;
				try {
					const event = JSON.parse(line.slice(5).trim());
					if (event.event === 'start') total = event.total;
					if (event.event === 'progress') {
						done = event.done;
						kept = event.kept ?? kept;
						dropped = event.dropped ?? dropped;
						if (event.warning) warning = event.warning;
					}
					if (event.event === 'done') {
						kept = event.kept ?? kept;
						dropped = event.dropped ?? dropped;
						finished = true;
					}
				} catch {}
			}
		}
		running = false;
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card>
		<StepHeader step={2} title="Verify &amp; generate" description="Local prefilter → MillionVerifier gate (ok only) → enrich → Claude draft. Only verified contacts cost credits." />

		{#if !running && !finished}
			<button
				onclick={startPrep}
				class="w-full py-3 bg-neutral-900 text-white rounded-lg text-sm font-medium"
			>
				Start verification + generation
			</button>
		{:else}
			<div class="space-y-4">
				<ProgressLine value={done} max={total || 1} label="contacts processed" />
				<div class="flex gap-6 text-sm text-neutral-500">
					<span><span class="font-medium text-neutral-900">{done}</span> processed</span>
					<span><span class="font-medium text-green-700">{kept}</span> kept</span>
					<span><span class="font-medium text-red-500">{dropped}</span> dropped</span>
					<span class="ml-auto text-neutral-400">{total} total</span>
				</div>
			</div>

			{#if warning}
				<div class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
					⚠️ {warning}
				</div>
			{/if}

			{#if finished}
				<div class="mt-6 pt-6 border-t border-neutral-100">
					<p class="text-sm text-neutral-500 mb-4">
						Done — <strong>{kept}</strong> emails drafted, <strong>{dropped}</strong> contacts dropped.
					</p>
					<div class="flex justify-end">
						<button
							onclick={() => goto(`/campaigns/${id}/sample`)}
							class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium"
						>
							Review sample →
						</button>
					</div>
				</div>
			{/if}
		{/if}

		{#if error}
			<p class="text-xs text-red-500 mt-3">{error}</p>
		{/if}
	</Card>
</div>
