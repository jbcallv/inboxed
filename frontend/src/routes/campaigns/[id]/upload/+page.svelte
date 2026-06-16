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
	let csvHeaders = $state<string[]>([]);
	let mapping = $state<Record<string, string>>({});
	let count = $state<number | null>(null);
	let uploading = $state(false);
	let error = $state('');
	let limit = $state<number | null>(null);
	let confirmed = $state(false);

	const DB_FIELDS: { key: string; label: string; required?: boolean }[] = [
		{ key: 'email', label: 'Email', required: true },
		{ key: 'first_name', label: 'First name' },
		{ key: 'last_name', label: 'Last name' },
		{ key: 'company_name', label: 'Company' },
		{ key: 'company_website', label: 'Website' },
		{ key: 'position', label: 'Job title' },
		{ key: 'bio', label: 'Bio / summary' },
	];

	const ALIASES: Record<string, string[]> = {
		email: ['email', 'email address', 'e-mail', 'emailaddress'],
		first_name: ['first name', 'firstname', 'first', 'given name', 'given_name'],
		last_name: ['last name', 'lastname', 'last', 'surname', 'family name', 'family_name'],
		company_name: ['company', 'company name', 'organization', 'organisation', 'org'],
		company_website: ['website', 'company website', 'url', 'site'],
		position: ['title', 'job title', 'jobtitle', 'role', 'position'],
		bio: ['bio', 'about', 'description', 'summary', 'matchmaking_message'],
	};

	function autoDetect(headers: string[]): Record<string, string> {
		const result: Record<string, string> = {};
		const lower = Object.fromEntries(headers.map(h => [h.toLowerCase().trim(), h]));
		for (const [field, aliases] of Object.entries(ALIASES)) {
			for (const alias of aliases) {
				if (lower[alias]) {
					result[field] = lower[alias];
					break;
				}
			}
		}
		return result;
	}

	async function parseHeaders(f: File): Promise<string[]> {
		const chunk = await f.slice(0, 4096).text();
		const firstLine = chunk.split('\n')[0];
		return firstLine.split(',').map(h => h.replace(/^"|"$/g, '').trim()).filter(Boolean);
	}

	onMount(async () => {
		const campaign = await get(`/api/campaigns/${id}`).catch(() => null);
		existingCount = campaign?.total ?? 0;
	});

	async function onFile(f: File) {
		file = f;
		error = '';
		const headers = await parseHeaders(f);
		csvHeaders = headers;
		mapping = autoDetect(headers);
	}

	async function upload() {
		if (!file) return;
		uploading = true;
		error = '';
		try {
			const form = new FormData();
			form.append('file', file);
			if (limit) form.append('limit', String(limit));
			const cleanMap = Object.fromEntries(
				Object.entries(mapping).filter(([, v]) => v && v !== '__skip__')
			);
			form.append('column_map', JSON.stringify(cleanMap));
			const result = await postForm(`/api/campaigns/${id}/upload`, form);
			count = result.imported;
		} catch (e: any) {
			error = e.message;
		} finally {
			uploading = false;
		}
	}

	const canUpload = $derived(
		!!file && !!mapping['email'] && mapping['email'] !== '__skip__'
	);
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card>
		<StepHeader step={1} title="Upload contacts" description="Drop a CSV — then confirm how columns map to contact fields." />

		{#if count === null}
			{#if existingCount > 0 && !confirmed}
				<div class="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mb-4">
					<p class="font-medium mb-1">This campaign already has {existingCount.toLocaleString()} contacts.</p>
					<p class="mb-3">Uploading again will add more rows on top of the existing ones.</p>
					<button
						onclick={() => confirmed = true}
						class="px-3 py-1.5 bg-amber-800 text-white rounded text-xs font-medium">
						I understand, add anyway
					</button>
				</div>
			{:else if !file}
				<div class="flex justify-end mb-3">
					<LimitInput bind:value={limit} placeholder="All rows" />
				</div>
				<DropZone onfile={onFile} />
			{:else}
				<!-- Field mapper -->
				<div class="mb-4 flex items-center justify-between">
					<p class="text-xs font-medium text-neutral-500">{file.name}</p>
					<button onclick={() => { file = null; csvHeaders = []; mapping = {}; }}
						class="text-xs text-neutral-400 hover:text-neutral-600">
						Change file
					</button>
				</div>

				<div class="border border-neutral-200 rounded-lg overflow-hidden mb-5">
					<div class="grid grid-cols-2 bg-neutral-50 border-b border-neutral-200 px-4 py-2">
						<p class="text-xs font-medium text-neutral-400 uppercase tracking-wide">Field</p>
						<p class="text-xs font-medium text-neutral-400 uppercase tracking-wide">CSV column</p>
					</div>
					{#each DB_FIELDS as field, i}
						<div class="grid grid-cols-2 items-center px-4 py-2.5 {i % 2 === 0 ? 'bg-white' : 'bg-neutral-50/50'}">
							<div class="flex items-center gap-1.5">
								<span class="text-sm text-neutral-700">{field.label}</span>
								{#if field.required}
									<span class="text-xs text-red-400">required</span>
								{/if}
							</div>
							<select
								bind:value={mapping[field.key]}
								class="text-sm border border-neutral-200 rounded-md px-2 py-1 bg-white text-neutral-700 focus:outline-none focus:ring-1 focus:ring-neutral-400 w-full">
								<option value="__skip__">— skip —</option>
								{#each csvHeaders as header}
									<option value={header}>{header}</option>
								{/each}
							</select>
						</div>
					{/each}
				</div>

				<div class="flex items-center justify-between">
					<LimitInput bind:value={limit} placeholder="All rows" />
					<button
						onclick={upload}
						disabled={!canUpload || uploading}
						class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed">
						{uploading ? 'Uploading…' : 'Upload contacts'}
					</button>
				</div>

				{#if error}
					<p class="text-xs text-red-500 mt-3 text-center">{error}</p>
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
					class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium">
					Continue to verify →
				</button>
			</div>
		{/if}
		<StepNav campaignId={id} next={{ href: `/campaigns/${id}/verify`, label: 'Verify emails' }} />
	</Card>
</div>
