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
	let loading = $state(true);

	onMount(async () => {
		emails = await get(`/api/campaigns/${id}/sample?n=5`).catch(() => []);
		loading = false;
	});

	async function approve() {
		await post(`/api/campaigns/${id}/launch`);
		goto(`/campaigns/${id}/monitor`);
	}

	async function skip() {
		await post(`/api/campaigns/${id}/launch`);
		goto(`/campaigns/${id}/monitor`);
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card class="mb-6">
		<StepHeader step={3} title="Review sample" description="A sample of generated emails. Approve to launch, or skip review entirely." />
		<div class="flex gap-3">
			<button
				onclick={approve}
				class="flex-1 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium"
			>
				Approve all and launch
			</button>
			<button
				onclick={skip}
				class="px-4 py-2 border border-neutral-200 text-neutral-600 rounded-lg text-sm"
			>
				Skip review
			</button>
		</div>
	</Card>

	{#if loading}
		<p class="text-sm text-neutral-400 text-center py-8">Loading sample…</p>
	{:else if emails.length === 0}
		<p class="text-sm text-neutral-400 text-center py-8">No generated emails yet. Verify contacts first.</p>
	{:else}
		<div class="space-y-4">
			{#each emails as email}
				<EmailPreviewCard {email} />
			{/each}
		</div>
	{/if}
</div>
