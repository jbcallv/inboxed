<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { get, post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import DomainCard from '$lib/components/DomainCard.svelte';
	import StepNav from '$lib/components/StepNav.svelte';

	const id = $derived($page.params.id);
	let domains = $state<any[]>([]);
	let suggestions = $state<any[]>([]);
	let baseName = $state('');
	let newDomain = $state({ domain: '', from_name: '', from_locals: '' });
	let searching = $state(false);
	let adding = $state(false);
	let addOpen = $state(false);
	let suggestOpen = $state(false);

	const hasDomains = $derived(domains.length > 0);

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
		if (!newDomain.domain || !newDomain.from_name) return;
		adding = true;
		await post('/api/domains', {
			domain: newDomain.domain,
			from_name: newDomain.from_name,
			from_locals: newDomain.from_locals.split(',').map((s: string) => s.trim()).filter(Boolean)
		});
		domains = await get('/api/domains').catch(() => []);
		newDomain = { domain: '', from_name: '', from_locals: '' };
		adding = false;
		addOpen = false;
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card class="mb-6">
		<StepHeader
			step={4}
			title="Sending domains"
			description="Each domain sends up to 250/day at steady state. 15–20 domains = ~4,500/day. Speed scales with domain count only."
		/>

		{#if !hasDomains}
			<div class="p-4 bg-neutral-50 border border-neutral-200 rounded-lg text-sm text-neutral-600 mb-6">
				No sending domains configured. Add at least one domain that is verified in Resend before launching.
			</div>
		{/if}

		<!-- Existing domains -->
		<div class="space-y-3 mb-6">
			{#each domains as domain}
				<DomainCard {domain} />
			{/each}
		</div>

		<!-- Find available domains -->
		<div class="border border-neutral-100 rounded-lg mb-3">
			<button
				onclick={() => { suggestOpen = !suggestOpen; }}
				class="w-full text-left px-4 py-3 text-sm font-medium text-neutral-700 flex justify-between items-center"
			>
				<span>Find available domains</span>
				<span class="text-neutral-400 text-xs">{suggestOpen ? '▲' : '▼'}</span>
			</button>
			{#if suggestOpen}
				<div class="px-4 pb-4 border-t border-neutral-100">
					<p class="text-xs text-neutral-400 mt-3 mb-2">Enter a base name (e.g. your brand) — we'll generate variants and check availability via Domainr.</p>
					<div class="flex gap-2">
						<input bind:value={baseName} placeholder="e.g. eximo, inboxed, getreach"
							class="flex-1 border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400" />
						<button onclick={suggest} disabled={searching || !baseName.trim()}
							class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-50">
							{searching ? 'Searching…' : 'Search'}
						</button>
					</div>
					{#if suggestions.length > 0}
						<p class="text-xs text-neutral-400 mt-3 mb-2">Click a domain to pre-fill the form below:</p>
						<div class="flex flex-wrap gap-2">
							{#each suggestions as s}
								<button
									onclick={() => { newDomain.domain = s.domain; addOpen = true; suggestOpen = false; }}
									class="text-xs px-3 py-1.5 border border-green-200 bg-green-50 text-green-800 rounded-full hover:bg-green-100 transition-colors">
									{s.domain}
								</button>
							{/each}
						</div>
					{:else if !searching && baseName}
						<p class="text-xs text-neutral-400 mt-3">No available domains found. Try a different name.</p>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Add domain form -->
		<div class="border border-neutral-100 rounded-lg">
			<button
				onclick={() => { addOpen = !addOpen; }}
				class="w-full text-left px-4 py-3 text-sm font-medium text-neutral-700 flex justify-between items-center"
			>
				<span>+ Add domain to pool</span>
				<span class="text-neutral-400 text-xs">{addOpen ? '▲' : '▼'}</span>
			</button>
			{#if addOpen}
				<div class="px-4 pb-4 border-t border-neutral-100 space-y-2 mt-3">
					<p class="text-xs text-neutral-400 mb-1">Domain must already be verified in Resend with SPF/DKIM/DMARC set.</p>
					<input bind:value={newDomain.domain} placeholder="Domain (e.g. geteximo.com)"
						class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
					<input bind:value={newDomain.from_name} placeholder="From name (e.g. Joseph at Eximo)"
						class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
					<input bind:value={newDomain.from_locals} placeholder="Local parts, comma-separated (e.g. joseph, hello, team)"
						class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
					<button onclick={addDomain} disabled={adding || !newDomain.domain || !newDomain.from_name}
						class="w-full py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-50 mt-1">
						{adding ? 'Adding…' : 'Add to pool'}
					</button>
				</div>
			{/if}
		</div>
	</Card>

	<StepNav
		campaignId={id}
		prev={{ href: `/campaigns/${id}/sample`, label: '← Review sample' }}
		next={{ href: `/campaigns/${id}/monitor`, label: 'Monitor', disabled: !hasDomains }}
	/>
</div>
