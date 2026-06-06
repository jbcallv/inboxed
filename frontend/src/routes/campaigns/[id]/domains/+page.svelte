<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import DomainCard from '$lib/components/DomainCard.svelte';

	const id = $derived($page.params.id);
	let domains = $state<any[]>([]);
	let suggestions = $state<any[]>([]);
	let baseName = $state('');
	let newDomain = $state({ domain: '', from_name: '', from_locals: '' });
	let searching = $state(false);
	let adding = $state(false);

	onMount(async () => {
		domains = await get('/api/domains').catch(() => []);
	});

	async function suggest() {
		if (!baseName.trim()) return;
		searching = true;
		suggestions = await post('/api/domains/suggest', { base_name: baseName }).catch(() => []);
		searching = false;
	}

	async function addDomain() {
		adding = true;
		await post('/api/domains', {
			domain: newDomain.domain,
			from_name: newDomain.from_name,
			from_locals: newDomain.from_locals.split(',').map((s: string) => s.trim()).filter(Boolean)
		});
		domains = await get('/api/domains').catch(() => []);
		newDomain = { domain: '', from_name: '', from_locals: '' };
		adding = false;
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card class="mb-6">
		<StepHeader step={4} title="Sending domains" description="15–20 warmed domains gives you ~4 500 sends/day at steady state. Speed = domain count." />

		<div class="space-y-3 mb-6">
			{#each domains as domain}
				<DomainCard {domain} />
			{/each}
			{#if domains.length === 0}
				<p class="text-sm text-neutral-400">No domains yet. Add one below.</p>
			{/if}
		</div>

		<details class="mb-4">
			<summary class="text-xs text-neutral-500 cursor-pointer">Suggest available domains</summary>
			<div class="mt-3 flex gap-2">
				<input bind:value={baseName} placeholder="base name, e.g. inboxed"
					class="flex-1 border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
				<button onclick={suggest} disabled={searching}
					class="px-3 py-2 border border-neutral-200 rounded-lg text-sm disabled:opacity-50">
					{searching ? '…' : 'Search'}
				</button>
			</div>
			{#if suggestions.length > 0}
				<div class="mt-3 flex flex-wrap gap-2">
					{#each suggestions.filter(s => s.available) as s}
						<button onclick={() => { newDomain.domain = s.domain; }}
							class="text-xs px-2 py-1 border border-neutral-200 rounded hover:bg-neutral-50">
							{s.domain}
						</button>
					{/each}
				</div>
			{/if}
		</details>

		<details>
			<summary class="text-xs text-neutral-500 cursor-pointer">Add domain manually</summary>
			<div class="mt-3 space-y-2">
				<input bind:value={newDomain.domain} placeholder="getinboxed.com"
					class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
				<input bind:value={newDomain.from_name} placeholder="From name (e.g. Joseph)"
					class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
				<input bind:value={newDomain.from_locals} placeholder="Local parts, comma-separated: joseph, hello, team"
					class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
				<button onclick={addDomain} disabled={adding || !newDomain.domain}
					class="w-full py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-50">
					{adding ? 'Adding…' : 'Add domain'}
				</button>
			</div>
		</details>
	</Card>

	<div class="flex justify-end">
		<button onclick={() => goto(`/campaigns/${id}/monitor`)}
			class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium">
			Continue →
		</button>
	</div>
</div>
