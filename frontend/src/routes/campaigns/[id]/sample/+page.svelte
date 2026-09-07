<script lang="ts">
	import { onMount } from 'svelte';
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
	let sampleSize = $state(5);

	let error = $state('');
	let clearing = $state(false);
	let cleared = $state(false);
	const hasEmails = $derived(emails.length > 0);

	async function clearGenerated() {
		if (
			!confirm(
				'Clear all generated emails for this campaign? You can regenerate with a new prompt afterward.'
			)
		)
			return;
		clearing = true;
		error = '';
		try {
			await post(`/api/campaigns/${id}/generate/reset`);
			emails = [];
			cleared = true;
		} catch (e: any) {
			error = e.message ?? 'Failed to clear generated emails';
		}
		clearing = false;
	}

	async function loadSample() {
		loading = true;
		error = '';
		try {
			emails = await get(`/api/campaigns/${id}/sample?n=${sampleSize}`);
		} catch (e: any) {
			error = e.message ?? 'Failed to load sample';
			emails = [];
		}
		loading = false;
	}

	onMount(loadSample);
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card class="mb-6">
		<StepHeader step={4} title="Review sample" description="A random sample of generated emails. Browse before configuring domains and launching." />

		{#if error}
			<div class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 mb-4">{error}</div>
		{:else if cleared}
			<div class="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 mb-4">
				Generated emails cleared.
				<a href={`/campaigns/${id}/generate`} class="underline font-medium">Go back to generate</a>
				with an updated prompt.
			</div>
		{:else if !loading && !hasEmails}
			<div class="p-3 bg-neutral-50 border border-neutral-200 rounded-lg text-sm text-neutral-600 mb-4">
				No emails generated yet. Return to step 3 to generate.
			</div>
		{/if}

		<div class="flex items-center gap-2">
			<span class="text-xs text-neutral-400">Show</span>
			{#each [3, 5, 10, 20] as n}
				<button
					onclick={() => { sampleSize = n; loadSample(); }}
					class="px-2.5 py-1 rounded text-xs font-medium border transition-colors
						{sampleSize === n
							? 'bg-neutral-900 text-white border-neutral-900'
							: 'bg-white text-neutral-500 border-neutral-200 hover:border-neutral-400'}"
				>{n}</button>
			{/each}
			<button
				onclick={loadSample}
				class="px-2.5 py-1 rounded text-xs border border-neutral-200 text-neutral-500 hover:border-neutral-400 transition-colors">
				Reshuffle
			</button>
			{#if hasEmails}
				<button
					onclick={clearGenerated}
					disabled={clearing}
					class="ml-auto px-2.5 py-1 rounded text-xs border border-red-200 text-red-600 hover:border-red-400 transition-colors disabled:opacity-50">
					{clearing ? 'Clearing…' : 'Clear generated emails'}
				</button>
			{/if}
		</div>
		<StepNav
			campaignId={id}
			prev={{ href: `/campaigns/${id}/generate`, label: '← Generate' }}
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
