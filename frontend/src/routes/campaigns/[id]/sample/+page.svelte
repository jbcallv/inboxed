<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import EmailPreviewCard from '$lib/components/EmailPreviewCard.svelte';
	import StepNav from '$lib/components/StepNav.svelte';

	const id = $derived($page.params.id);
	let emails = $state<any[]>([]);
	let domains = $state<any[]>([]);
	let loading = $state(true);

	const hasDomains = $derived(domains.length > 0);
	const hasEmails = $derived(emails.length > 0);
	const canLaunch = $derived(hasDomains && hasEmails);

	onMount(async () => {
		[emails, domains] = await Promise.all([
			get(`/api/campaigns/${id}/sample?n=5`).catch(() => []),
			get('/api/domains').catch(() => [])
		]);
		loading = false;
	});

	async function launch() {
		await post(`/api/campaigns/${id}/launch`);
		goto(`/campaigns/${id}`);
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card class="mb-6">
		<StepHeader step={3} title="Review sample" description="A sample of generated emails. Approve to queue them for sending." />

		{#if !loading}
			{#if !hasEmails}
				<div class="p-3 bg-neutral-50 border border-neutral-200 rounded-lg text-sm text-neutral-600 mb-4">
					No emails generated yet. Return to step 2 to run verification and generation.
				</div>
			{/if}
			{#if !hasDomains}
				<div class="p-3 bg-neutral-50 border border-neutral-200 rounded-lg text-sm text-neutral-600 mb-4">
					No sending domains configured.
					<a href="/campaigns/{id}/domains" class="underline font-medium">Add one in step 4</a>
					before launching.
				</div>
			{/if}
		{/if}

		<div class="flex gap-3">
			<button
				onclick={launch}
				disabled={!canLaunch}
				class="flex-1 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
			>
				{canLaunch ? 'Approve and launch' : 'Cannot launch yet'}
			</button>
		</div>
		<StepNav
			campaignId={id}
			prev={{ href: `/campaigns/${id}/verify`, label: '← Re-generate' }}
			next={{ href: `/campaigns/${id}/domains`, label: 'Configure domains' }}
		/>
	</Card>

	{#if loading}
		<p class="text-sm text-neutral-400 text-center py-8">Loading…</p>
	{:else if !hasEmails}
		<p class="text-sm text-neutral-400 text-center py-8">No emails to preview.</p>
	{:else}
		<div class="space-y-4">
			{#each emails as email}
				<EmailPreviewCard {email} />
			{/each}
		</div>
	{/if}
</div>
