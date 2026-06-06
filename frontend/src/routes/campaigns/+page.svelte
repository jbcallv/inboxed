<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores';
	import { get, post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';

	type Campaign = { id: string; name: string; status: string; created_at: string };
	let campaigns = $state<Campaign[]>([]);
	let newName = $state('');
	let creating = $state(false);

	$effect(() => { if (!$session) goto('/'); });

	onMount(async () => {
		campaigns = await get('/api/campaigns').catch(() => []);
	});

	async function create() {
		if (!newName.trim()) return;
		creating = true;
		const c = await post('/api/campaigns', { name: newName });
		goto(`/campaigns/${c.id}/upload`);
	}

	const statusColor: Record<string, string> = {
		draft:     'text-neutral-400',
		prepping:  'text-blue-500',
		ready:     'text-green-600',
		sending:   'text-green-700',
		done:      'text-neutral-400',
		paused:    'text-amber-600',
	};
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<div class="flex items-baseline justify-between mb-8">
		<h1 class="text-xl font-semibold text-neutral-900">Campaigns</h1>
	</div>

	<Card class="mb-6">
		<form onsubmit={(e) => { e.preventDefault(); create(); }} class="flex gap-3">
			<input
				bind:value={newName}
				placeholder="New campaign name"
				class="flex-1 border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400"
			/>
			<button
				type="submit"
				disabled={creating || !newName.trim()}
				class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-50"
			>
				Create
			</button>
		</form>
	</Card>

	{#each campaigns as c}
		<a href="/campaigns/{c.id}" class="block mb-2">
			<div class="border border-neutral-200 rounded-lg bg-white px-5 py-4 hover:border-neutral-300 transition-colors flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-neutral-900">{c.name}</p>
					<p class="text-xs mt-0.5 {statusColor[c.status] ?? 'text-neutral-400'}">{c.status}</p>
				</div>
				<span class="text-neutral-300 text-sm">→</span>
			</div>
		</a>
	{/each}

	{#if campaigns.length === 0}
		<p class="text-sm text-neutral-400 text-center py-10">No campaigns yet. Create one above.</p>
	{/if}
</div>
