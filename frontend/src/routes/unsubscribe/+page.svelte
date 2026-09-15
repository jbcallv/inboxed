<script lang="ts">
	import { page } from '$app/stores';
	import { post } from '$lib/api';
	import Card from '$lib/components/Card.svelte';

	const email = $derived($page.url.searchParams.get('email') ?? '');
	const campaignId = $derived($page.url.searchParams.get('campaign') ?? '');

	let status = $state<'idle' | 'working' | 'done' | 'error'>('idle');
	let errorMessage = $state('');

	async function confirm() {
		status = 'working';
		errorMessage = '';
		try {
			await post('/api/unsubscribe', { email, campaign_id: campaignId });
			status = 'done';
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Something went wrong.';
			status = 'error';
		}
	}
</script>

<div class="max-w-sm mx-auto py-24 px-4">
	<Card>
		{#if !email || !campaignId}
			<p class="text-sm text-neutral-600">This unsubscribe link is missing information. Please use the link from the original email.</p>
		{:else if status === 'done'}
			<h1 class="text-lg font-semibold text-neutral-900 mb-1">You're unsubscribed</h1>
			<p class="text-sm text-neutral-500">{email} won't receive any further emails from this campaign.</p>
		{:else if status === 'error'}
			<h1 class="text-lg font-semibold text-neutral-900 mb-1">Couldn't process that</h1>
			<p class="text-sm text-neutral-500 mb-4">{errorMessage}</p>
			<button onclick={confirm}
				class="w-full py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium">
				Try again
			</button>
		{:else}
			<h1 class="text-lg font-semibold text-neutral-900 mb-1">Unsubscribe</h1>
			<p class="text-sm text-neutral-500 mb-4">Confirm you'd like to stop receiving emails at <span class="font-medium text-neutral-700">{email}</span>.</p>
			<button onclick={confirm} disabled={status === 'working'}
				class="w-full py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-50">
				{status === 'working' ? 'Unsubscribing…' : 'Unsubscribe me'}
			</button>
		{/if}
	</Card>
</div>
