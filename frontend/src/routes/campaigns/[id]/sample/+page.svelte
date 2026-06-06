<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import EmailPreviewCard from '$lib/components/EmailPreviewCard.svelte';

	const id = $derived($page.params.id);
	let emails = $state<any[]>([]);
	let domains = $state<any[]>([]);
	let loading = $state(true);

	const hasDomains = $derived(domains.length > 0);

	onMount(async () => {
		[emails, domains] = await Promise.all([
			get(`/api/campaigns/${id}/sample?n=5`).catch(() => []),
			get('/api/domains').catch(() => [])
		]);
		loading = false;
	});

	async function launch() {
		await post(`/api/campaigns/${id}/launch`);
		goto(`/campaigns/${id}/monitor`);
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card class="mb-6">
		<StepHeader step={3} title="Review sample" description="A sample of generated emails. Approve to queue them for sending, or skip straight through." />

		{#if !hasDomains}
			<div class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mb-4">
				⚠️ No sending domains configured yet —
				<a href="/campaigns/{id}/domains" class="underline font-medium">add one first</a>
				before launching.
			</div>
		{/if}

		<div class="flex gap-3">
			<button
				onclick={launch}
				disabled={!hasDomains}
				class="flex-1 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
			>
				{hasDomains ? 'Approve all and launch' : 'Add a domain first'}
			</button>
			<button
				onclick={() => goto(`/campaigns/${id}/domains`)}
				class="px-4 py-2 border border-neutral-200 text-neutral-600 rounded-lg text-sm"
			>
				Configure domains →
			</button>
		</div>
	</Card>

	{#if loading}
		<p class="text-sm text-neutral-400 text-center py-8">Loading sample…</p>
	{:else if emails.length === 0}
		<Card>
			<p class="text-sm text-neutral-500 text-center py-4">
				No emails generated yet. Make sure verification and generation completed successfully in step 2.
			</p>
		</Card>
	{:else}
		<div class="space-y-4">
			{#each emails as email}
				<EmailPreviewCard {email} />
			{/each}
		</div>
	{/if}
</div>
