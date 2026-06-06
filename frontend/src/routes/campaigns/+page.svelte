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
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<div class="flex items-baseline justify-between mb-10">
		<h1 class="text-2xl font-semibold text-neutral-900">Campaigns</h1>
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
				disabled={creating}
				class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-50"
			>
				Create
			</button>
		</form>
	</Card>

	{#each campaigns as c}
		<a href="/campaigns/{c.id}/upload" class="block mb-3">
			<Card class="hover:border-neutral-300 transition-colors cursor-pointer">
				<div class="flex items-center justify-between">
					<div>
						<p class="font-medium text-sm text-neutral-900">{c.name}</p>
						<p class="text-xs text-neutral-400 mt-0.5">{c.status}</p>
					</div>
					<span class="text-neutral-300">→</span>
				</div>
			</Card>
		</a>
	{/each}

	{#if campaigns.length === 0}
		<p class="text-sm text-neutral-400 text-center py-8">No campaigns yet. Create one above.</p>
	{/if}
</div>
