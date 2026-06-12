<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { get, post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import StatPill from '$lib/components/StatPill.svelte';
	import DomainCard from '$lib/components/DomainCard.svelte';
	import StepNav from '$lib/components/StepNav.svelte';

	const id = $derived($page.params.id);
	let stats = $state<any>(null);
	let domains = $state<any[]>([]);
	let interval: number;

	async function refresh() {
		[stats, domains] = await Promise.all([
			get(`/api/campaigns/${id}/stats`).catch(() => null),
			get(`/api/domains?campaign_id=${id}`).catch(() => [])
		]);
	}

	onMount(() => {
		refresh();
		interval = setInterval(refresh, 30_000);
	});

	onDestroy(() => clearInterval(interval));

	async function launch() {
		await post(`/api/campaigns/${id}/launch`);
		refresh();
	}

	async function pause() {
		await post(`/api/campaigns/${id}/pause`);
		refresh();
	}

	async function resume() {
		await post(`/api/campaigns/${id}/resume`);
		refresh();
	}

	const isPaused = $derived(stats?.status === 'paused');
	const isSending = $derived(stats?.status === 'sending');
	const isReady = $derived(stats?.status === 'ready');
	const hasDomains = $derived(domains.length > 0);
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card class="mb-6">
		<StepHeader step={6} title="Launch & monitor" description="Launch to queue all drafted emails. The worker sends autonomously. Updates every 30 seconds." />

		{#if stats}
			<div class="flex flex-wrap gap-3 justify-center mb-6">
				<StatPill label="sent" value={stats.status_counts?.sent ?? 0} />
				<StatPill label="queued" value={stats.status_counts?.queued ?? 0} />
				<StatPill label="replies" value={stats.replies ?? 0} />
				<StatPill label="hot leads" value={stats.hot_leads ?? 0} />
				<StatPill label="rejected" value={stats.status_counts?.rejected ?? 0} />
				<StatPill label="total" value={stats.total ?? 0} />
			</div>
		{:else}
			<p class="text-sm text-neutral-400 mb-6">Loading stats…</p>
		{/if}

		<div class="flex justify-end gap-2">
			{#if isReady}
				{#if !hasDomains}
					<p class="text-xs text-amber-600 self-center mr-2">Configure a sending domain first</p>
				{/if}
				<button onclick={launch} disabled={!hasDomains}
					class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed">
					Launch campaign
				</button>
			{:else if isPaused}
				<button onclick={resume}
					class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium">
					Resume sending
				</button>
			{:else if isSending}
				<button onclick={pause}
					class="px-4 py-2 border border-neutral-200 text-neutral-600 rounded-lg text-sm hover:bg-neutral-50">
					Pause campaign
				</button>
			{/if}
		</div>
		<StepNav campaignId={id} prev={{ href: `/campaigns/${id}/domains`, label: '← Domains' }} />
	</Card>

	<h3 class="text-xs font-medium text-neutral-400 uppercase tracking-widest mb-3">Domain pool</h3>
	<div class="space-y-3">
		{#each domains as domain}
			<DomainCard {domain} onStatusChange={refresh} />
		{/each}
		{#if domains.length === 0}
			<p class="text-sm text-neutral-400">No domains configured.</p>
		{/if}
	</div>
</div>
