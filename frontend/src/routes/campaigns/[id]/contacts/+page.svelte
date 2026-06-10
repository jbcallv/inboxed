<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { get } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepNav from '$lib/components/StepNav.svelte';

	const id = $derived($page.params.id);

	const STATUSES = ['all', 'new', 'finding', 'verifying', 'enriching', 'generating', 'drafted', 'queued', 'sent', 'rejected', 'no_email'];

	let contacts = $state<any[]>([]);
	let selectedStatus = $state('all');
	let loading = $state(true);
	let currentPage = $state(1);
	const PAGE_SIZE = 50;

	async function load() {
		loading = true;
		const params = new URLSearchParams({ page: String(currentPage), limit: String(PAGE_SIZE) });
		if (selectedStatus !== 'all') params.set('status', selectedStatus);
		contacts = await get(`/api/campaigns/${id}/contacts?${params}`).catch(() => []);
		loading = false;
	}

	onMount(load);

	function selectStatus(s: string) {
		selectedStatus = s;
		currentPage = 1;
		load();
	}

	const statusColor: Record<string, string> = {
		sent: 'bg-green-100 text-green-800',
		drafted: 'bg-blue-100 text-blue-800',
		queued: 'bg-yellow-100 text-yellow-800',
		rejected: 'bg-red-100 text-red-800',
		no_email: 'bg-red-100 text-red-800',
		new: 'bg-neutral-100 text-neutral-600',
		verifying: 'bg-purple-100 text-purple-800',
		generating: 'bg-purple-100 text-purple-800',
		finding: 'bg-orange-100 text-orange-800',
		enriching: 'bg-orange-100 text-orange-800',
	};
</script>

<div class="max-w-4xl mx-auto py-12 px-4">
	<div class="mb-6">
		<h1 class="text-xl font-semibold text-neutral-900">Contacts</h1>
		<p class="text-xs text-neutral-400 mt-0.5">Showing {contacts.length} contacts</p>
	</div>

	<!-- Status filter -->
	<div class="flex flex-wrap gap-2 mb-6">
		{#each STATUSES as s}
			<button
				onclick={() => selectStatus(s)}
				class="px-3 py-1 rounded-full text-xs font-medium border transition-colors
					{selectedStatus === s
						? 'bg-neutral-900 text-white border-neutral-900'
						: 'bg-white text-neutral-600 border-neutral-200 hover:border-neutral-400'}"
			>
				{s}
			</button>
		{/each}
	</div>

	<Card>
		{#if loading}
			<p class="text-sm text-neutral-400 py-6 text-center">Loading…</p>
		{:else if contacts.length === 0}
			<p class="text-sm text-neutral-400 py-6 text-center">No contacts match this filter.</p>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-neutral-100">
							<th class="text-left py-2 pr-4 text-xs font-medium text-neutral-400 uppercase tracking-wide">Name</th>
							<th class="text-left py-2 pr-4 text-xs font-medium text-neutral-400 uppercase tracking-wide">Company</th>
							<th class="text-left py-2 pr-4 text-xs font-medium text-neutral-400 uppercase tracking-wide">Email</th>
							<th class="text-left py-2 pr-4 text-xs font-medium text-neutral-400 uppercase tracking-wide">Role</th>
							<th class="text-left py-2 text-xs font-medium text-neutral-400 uppercase tracking-wide">Status</th>
						</tr>
					</thead>
					<tbody>
						{#each contacts as c}
							<tr class="border-b border-neutral-50 hover:bg-neutral-50 transition-colors">
								<td class="py-2.5 pr-4 font-medium text-neutral-900">
									{c.first_name ?? ''} {c.last_name ?? ''}
								</td>
								<td class="py-2.5 pr-4 text-neutral-600">{c.company_name ?? '—'}</td>
								<td class="py-2.5 pr-4 text-neutral-500 font-mono text-xs">{c.email ?? '—'}</td>
								<td class="py-2.5 pr-4 text-neutral-500 max-w-[160px] truncate">{c.position ?? '—'}</td>
								<td class="py-2.5">
									<span class="px-2 py-0.5 rounded-full text-xs font-medium {statusColor[c.status] ?? 'bg-neutral-100 text-neutral-600'}">
										{c.status}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			{#if contacts.length === PAGE_SIZE}
				<div class="flex justify-between items-center mt-4 pt-4 border-t border-neutral-100">
					<button
						onclick={() => { currentPage--; load(); }}
						disabled={currentPage === 1}
						class="text-sm text-neutral-500 disabled:opacity-30 hover:text-neutral-900 transition-colors">
						← Prev
					</button>
					<span class="text-xs text-neutral-400">Page {currentPage}</span>
					<button
						onclick={() => { currentPage++; load(); }}
						class="text-sm text-neutral-500 hover:text-neutral-900 transition-colors">
						Next →
					</button>
				</div>
			{/if}
		{/if}
		<StepNav campaignId={id} />
	</Card>
</div>
