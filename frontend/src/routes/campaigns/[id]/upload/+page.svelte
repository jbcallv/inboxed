<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, postForm } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import DropZone from '$lib/components/DropZone.svelte';
	import StepNav from '$lib/components/StepNav.svelte';
	import LimitInput from '$lib/components/LimitInput.svelte';

	const id = $derived($page.params.id);
	let existingCount = $state(0);
	let file = $state<File | null>(null);
	let count = $state<number | null>(null);
	let uploading = $state(false);
	let error = $state('');
	let limit = $state<number | null>(null);
	let confirmed = $state(false);

	onMount(async () => {
		const campaign = await get(`/api/campaigns/${id}`).catch(() => null);
		existingCount = campaign?.total ?? 0;
	});

	const needsConfirm = $derived(existingCount > 0 && !confirmed);

	async function upload() {
		if (!file) return;
		uploading = true;
		error = '';
		try {
			const form = new FormData();
			form.append('file', file);
			if (limit) form.append('limit', String(limit));
			const result = await postForm(`/api/campaigns/${id}/upload`, form);
			count = result.imported;
		} catch (e: any) {
			error = e.message;
		} finally {
			uploading = false;
		}
	}

	function onFile(f: File) {
		file = f;
		upload();
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card>
		<StepHeader step={1} title="Upload contacts" description="Drop a CSV or XLSX with at least email or first + last name + company website." />

		{#if count === null}
			{#if existingCount > 0 && !confirmed}
				<div class="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mb-4">
					<p class="font-medium mb-1">This campaign already has {existingCount.toLocaleString()} contacts.</p>
					<p class="mb-3">Uploading again will add more rows on top of the existing ones. Clear the campaign first if you want to start fresh.</p>
					<button
						onclick={() => confirmed = true}
						class="px-3 py-1.5 bg-amber-800 text-white rounded text-xs font-medium">
						I understand, add anyway
					</button>
				</div>
			{:else}
				<div class="flex justify-end mb-3">
					<LimitInput bind:value={limit} placeholder="All rows" />
				</div>
				<DropZone onfile={onFile} />
				{#if file}
					<p class="text-xs text-neutral-400 mt-3 text-center">{file.name} — {uploading ? 'uploading…' : ''}</p>
				{/if}
				{#if error}
					<p class="text-xs text-red-500 mt-2 text-center">{error}</p>
				{/if}
			{/if}
		{:else}
			<div class="text-center py-6">
				<p class="text-3xl font-semibold text-neutral-900">{count.toLocaleString()}</p>
				<p class="text-sm text-neutral-400 mt-1">contacts imported</p>
			</div>
			<div class="flex justify-end mt-4">
				<button
					onclick={() => goto(`/campaigns/${id}/verify`)}
					class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium"
				>
					Continue to verify →
				</button>
			</div>
		{/if}
		<StepNav campaignId={id} next={{ href: `/campaigns/${id}/verify`, label: 'Verify emails' }} />
	</Card>
</div>
