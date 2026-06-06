<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { get, post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StatPill from '$lib/components/StatPill.svelte';
	import DomainCard from '$lib/components/DomainCard.svelte';

	const id = $derived($page.params.id);
	let campaign = $state<any>(null);
	let domains = $state<any[]>([]);
	let interval: number;

	async function refresh() {
		[campaign, domains] = await Promise.all([
			get(`/api/campaigns/${id}`).catch(() => null),
			get('/api/domains').catch(() => [])
		]);
	}

	onMount(() => {
		refresh();
		interval = setInterval(refresh, 30_000);
	});

	onDestroy(() => clearInterval(interval));

	async function pause() {
		await post(`/api/campaigns/${id}/pause`);
		refresh();
	}

	async function launch() {
		await post(`/api/campaigns/${id}/launch`);
		refresh();
	}

	const statusLabel: Record<string, string> = {
		draft: 'Draft',
		prepping: 'Prepping',
		ready: 'Ready to launch',
		sending: 'Sending',
		done: 'Done',
		paused: 'Paused',
	};
</script>

<div class="max-w-2xl mx-auto py-12 px-4">
	{#if campaign}
		<div class="flex items-baseline justify-between mb-8">
			<div>
				<h1 class="text-xl font-semibold text-neutral-900">{campaign.name}</h1>
				<p class="text-xs text-neutral-400 mt-0.5">{statusLabel[campaign.status] ?? campaign.status}</p>
			</div>
			<div class="flex gap-2">
				{#if campaign.status === 'ready'}
					<button onclick={launch}
						class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium">
						Launch sending
					</button>
				{:else if campaign.status === 'sending'}
					<button onclick={pause}
						class="px-4 py-2 border border-neutral-200 text-neutral-600 rounded-lg text-sm">
						Pause
					</button>
				{/if}
			</div>
		</div>

		<!-- Stats -->
		<Card class="mb-4">
			<p class="text-xs font-medium text-neutral-400 uppercase tracking-widest mb-4">Contact pipeline</p>
			<div class="flex flex-wrap gap-3">
				<StatPill label="sent" value={campaign.status_counts?.sent ?? 0} />
				<StatPill label="queued" value={campaign.status_counts?.queued ?? 0} />
				<StatPill label="drafted" value={campaign.status_counts?.drafted ?? 0} />
				<StatPill label="rejected" value={campaign.status_counts?.rejected ?? 0} />
				<StatPill label="no email" value={campaign.status_counts?.no_email ?? 0} />
				<StatPill label="total" value={campaign.total ?? 0} />
			</div>
		</Card>

		<!-- Domain pool -->
		<Card class="mb-6">
			<p class="text-xs font-medium text-neutral-400 uppercase tracking-widest mb-4">Domain pool</p>
			{#if domains.length === 0}
				<p class="text-sm text-neutral-400">No domains configured.</p>
			{:else}
				<div class="space-y-3">
					{#each domains as domain}
						<DomainCard {domain} />
					{/each}
				</div>
			{/if}
		</Card>

		<!-- Step nav -->
		<hr class="border-neutral-100 mb-6" />
		<p class="text-xs font-medium text-neutral-400 uppercase tracking-widest mb-3">Steps</p>
		<div class="grid grid-cols-2 gap-2">
			<a href="/campaigns/{id}/upload"
				class="block border border-neutral-200 rounded-lg px-4 py-3 text-sm text-neutral-700 hover:border-neutral-300 hover:bg-white transition-colors bg-neutral-50">
				Upload contacts
			</a>
			<a href="/campaigns/{id}/verify"
				class="block border border-neutral-200 rounded-lg px-4 py-3 text-sm text-neutral-700 hover:border-neutral-300 hover:bg-white transition-colors bg-neutral-50">
				Verify + generate
			</a>
			<a href="/campaigns/{id}/sample"
				class="block border border-neutral-200 rounded-lg px-4 py-3 text-sm text-neutral-700 hover:border-neutral-300 hover:bg-white transition-colors bg-neutral-50">
				Review sample
			</a>
			<a href="/campaigns/{id}/domains"
				class="block border border-neutral-200 rounded-lg px-4 py-3 text-sm text-neutral-700 hover:border-neutral-300 hover:bg-white transition-colors bg-neutral-50">
				Configure domains
			</a>
		</div>
	{:else}
		<p class="text-sm text-neutral-400">Loading…</p>
	{/if}
</div>
