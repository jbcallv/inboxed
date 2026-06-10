<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { postForm } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import DropZone from '$lib/components/DropZone.svelte';
	import StepNav from '$lib/components/StepNav.svelte';

	const id = $derived($page.params.id);
	let file = $state<File | null>(null);
	let count = $state<number | null>(null);
	let uploading = $state(false);
	let error = $state('');

	async function upload() {
		if (!file) return;
		uploading = true;
		error = '';
		try {
			const form = new FormData();
			form.append('file', file);
			const result = await postForm(`/api/campaigns/${id}/upload`, form);
			count = result.imported;
		} catch (e: any) {
			error = e.message;
		} finally {
			uploading = false;
		}
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card>
		<StepHeader step={1} title="Upload contacts" description="Drop a CSV or XLSX with at least email or first + last name + company website." />

		{#if count === null}
			<DropZone onfile={(f) => { file = f; upload(); }} />
			{#if file}
				<p class="text-xs text-neutral-400 mt-3 text-center">{file.name} — {uploading ? 'uploading…' : ''}</p>
			{/if}
			{#if error}
				<p class="text-xs text-red-500 mt-2 text-center">{error}</p>
			{/if}
		{:else}
			<div class="text-center py-6">
				<p class="text-3xl font-semibold text-neutral-900">{count}</p>
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
		<StepNav campaignId={id} next={{ href: `/campaigns/${id}/verify`, label: 'Verify + generate' }} />
	</Card>
</div>
