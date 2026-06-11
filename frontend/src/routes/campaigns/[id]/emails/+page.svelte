<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { get } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepNav from '$lib/components/StepNav.svelte';

	const id = $derived($page.params.id);

	const STATUS_FILTERS = [
		{ value: null, label: 'All sent' },
		{ value: 'sent', label: 'Sent' },
		{ value: 'replied', label: 'Replied' },
		{ value: 'hot_lead', label: 'Hot leads' },
		{ value: 'unsubscribed', label: 'Unsubscribed' },
		{ value: 'bounced', label: 'Bounced' },
	];

	const STATUS_COLORS: Record<string, string> = {
		sent: 'bg-blue-50 text-blue-700',
		replied: 'bg-green-50 text-green-700',
		hot_lead: 'bg-orange-50 text-orange-700',
		unsubscribed: 'bg-neutral-100 text-neutral-500',
		bounced: 'bg-red-50 text-red-700',
	};

	let emails = $state<any[]>([]);
	let loading = $state(false);
	let selectedStatus = $state<string | null>(null);
	let search = $state('');
	let page_num = $state(1);
	let total = $state(0);
	let expanded = $state<string | null>(null);
	let searchTimeout: ReturnType<typeof setTimeout>;

	const limit = 50;
	const totalPages = $derived(Math.ceil(total / limit));

	async function load() {
		loading = true;
		const params = new URLSearchParams({ page: String(page_num), limit: String(limit) });
		if (selectedStatus) params.set('status', selectedStatus);
		if (search.trim()) params.set('search', search.trim());

		const [rows, countData] = await Promise.all([
			get(`/api/campaigns/${id}/emails?${params}`).catch(() => []),
			get(`/api/campaigns/${id}/emails/count?${selectedStatus ? `status=${selectedStatus}` : ''}`).catch(() => ({ count: 0 })),
		]);
		emails = rows;
		total = countData.count ?? 0;
		loading = false;
	}

	function selectStatus(s: string | null) {
		selectedStatus = s;
		page_num = 1;
		load();
	}

	function onSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => { page_num = 1; load(); }, 300);
	}

	function contactName(e: any) {
		const name = [e.first_name, e.last_name].filter(Boolean).join(' ');
		return name || e.company_name || e.email;
	}

	function latestEmail(e: any) {
		return e.outreach_emails?.[0] ?? null;
	}

	function latestReply(e: any) {
		return e.responses?.[0] ?? null;
	}

	onMount(load);
</script>

<div class="max-w-4xl mx-auto py-12 px-4">
	<Card class="mb-6">
		<div class="p-6 border-b border-neutral-100">
			<h2 class="text-lg font-semibold text-neutral-900">Sent emails</h2>
			<p class="text-sm text-neutral-400 mt-1">{total} contacts</p>
		</div>

		<!-- Filters + search -->
		<div class="p-4 border-b border-neutral-100 flex flex-wrap gap-2 items-center">
			<div class="flex gap-1 flex-wrap">
				{#each STATUS_FILTERS as f}
					<button
						onclick={() => selectStatus(f.value)}
						class="px-3 py-1 rounded-full text-xs font-medium transition-colors
							{selectedStatus === f.value
								? 'bg-neutral-900 text-white'
								: 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'}"
					>
						{f.label}
					</button>
				{/each}
			</div>
			<input
				bind:value={search}
				oninput={onSearch}
				placeholder="Search by email…"
				class="ml-auto border border-neutral-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400 w-56"
			/>
		</div>

		<!-- Table -->
		{#if loading}
			<p class="text-sm text-neutral-400 p-6">Loading…</p>
		{:else if emails.length === 0}
			<p class="text-sm text-neutral-400 p-6">No emails found.</p>
		{:else}
			<div class="divide-y divide-neutral-100">
				{#each emails as entry (entry.id)}
					{@const email = latestEmail(entry)}
					{@const reply = latestReply(entry)}
					<div>
						<button
							onclick={() => expanded = expanded === entry.id ? null : entry.id}
							class="w-full text-left px-6 py-3 hover:bg-neutral-50 transition-colors"
						>
							<div class="flex items-center gap-3">
								<div class="flex-1 min-w-0">
									<p class="text-sm font-medium text-neutral-900 truncate">{contactName(entry)}</p>
									<p class="text-xs text-neutral-400 truncate">{entry.email}</p>
								</div>
								{#if email}
									<p class="text-xs text-neutral-500 flex-1 min-w-0 truncate hidden sm:block">{email.subject}</p>
								{/if}
								<span class="text-xs px-2 py-0.5 rounded-full font-medium {STATUS_COLORS[entry.status] ?? 'bg-neutral-100 text-neutral-500'}">
									{entry.status.replace('_', ' ')}
								</span>
								{#if reply}
									<span class="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700 font-medium">
										{reply.sentiment}
									</span>
								{/if}
								<span class="text-neutral-300 text-xs ml-1">{expanded === entry.id ? '▲' : '▼'}</span>
							</div>
						</button>

						{#if expanded === entry.id}
							<div class="px-6 pb-4 bg-neutral-50 border-t border-neutral-100 space-y-4">
								{#if email}
									<div class="pt-4">
										<p class="text-xs font-medium text-neutral-500 mb-1">Subject</p>
										<p class="text-sm text-neutral-800">{email.subject}</p>
										<p class="text-xs font-medium text-neutral-500 mt-3 mb-1">Body</p>
										<pre class="text-sm text-neutral-700 whitespace-pre-wrap font-sans">{email.body}</pre>
									</div>
								{/if}
								{#if reply}
									<div class="border-t border-neutral-200 pt-4">
										<p class="text-xs font-medium text-neutral-500 mb-1">
											Reply — <span class="text-green-700">{reply.sentiment}</span>
											{#if reply.received_at}
												· {new Date(reply.received_at).toLocaleDateString()}
											{/if}
										</p>
										<pre class="text-sm text-neutral-700 whitespace-pre-wrap font-sans">{reply.reply_body}</pre>
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<!-- Pagination -->
			{#if totalPages > 1}
				<div class="flex justify-between items-center px-6 py-3 border-t border-neutral-100">
					<button
						onclick={() => { page_num--; load(); }}
						disabled={page_num === 1}
						class="text-sm text-neutral-600 disabled:opacity-30"
					>← Prev</button>
					<span class="text-xs text-neutral-400">Page {page_num} of {totalPages}</span>
					<button
						onclick={() => { page_num++; load(); }}
						disabled={page_num >= totalPages}
						class="text-sm text-neutral-600 disabled:opacity-30"
					>Next →</button>
				</div>
			{/if}
		{/if}
	</Card>

	<StepNav campaignId={id} prev={{ href: `/campaigns/${id}/monitor`, label: '← Monitor' }} />
</div>
