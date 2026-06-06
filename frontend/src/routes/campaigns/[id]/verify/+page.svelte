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
	let finished = $state(false);
	let error = $state('');

	async function startPrep() {
		running = true;
		error = '';
		const token = await getToken();
		const res = await fetch(`${BASE}/api/campaigns/${id}/prep`, {
			method: 'POST',
			headers: token ? { Authorization: `Bearer ${token}` } : {}
		});

		const reader = res.body!.getReader();
		const decoder = new TextDecoder();

		while (true) {
			const { value, done: streamDone } = await reader.read();
			if (streamDone) break;
			const text = decoder.decode(value);
			for (const line of text.split('\n')) {
				if (!line.startsWith('data:')) continue;
				const event = JSON.parse(line.slice(5).trim());
				if (event.event === 'start') total = event.total;
				if (event.event === 'progress') done = event.done;
				if (event.event === 'done') finished = true;
			}
		}
		running = false;
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card>
		<StepHeader step={2} title="Verify contacts" description="Only MillionVerifier 'ok' results are kept. No credit spent on bad addresses." />

		{#if !running && !finished}
			<button
				onclick={startPrep}
				class="w-full py-3 bg-neutral-900 text-white rounded-lg text-sm font-medium"
			>
				Run verification + email generation
			</button>
		{:else}
			<div class="space-y-4">
				<ProgressLine value={done} max={total || 1} label="contacts processed" />
				<div class="flex justify-between text-sm text-neutral-500">
					<span>{done} processed</span>
					<span>{total} total</span>
				</div>
			</div>

			{#if finished}
				<div class="mt-6 pt-6 border-t border-neutral-100 flex justify-end">
					<button
						onclick={() => goto(`/campaigns/${id}/sample`)}
						class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium"
					>
						Review sample →
					</button>
				</div>
			{/if}
		{/if}

		{#if error}
			<p class="text-xs text-red-500 mt-3">{error}</p>
		{/if}
	</Card>
</div>
