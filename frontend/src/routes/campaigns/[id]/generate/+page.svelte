<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getToken } from '$lib/supabase';
	import { get, put } from '$lib/api';
	import Card from '$lib/components/Card.svelte';
	import StepHeader from '$lib/components/StepHeader.svelte';
	import ProgressLine from '$lib/components/ProgressLine.svelte';
	import StepNav from '$lib/components/StepNav.svelte';
	import LimitInput from '$lib/components/LimitInput.svelte';

	const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
	const id = $derived($page.params.id);

	let prompt = $state('');
	let defaultPrompt = $state('');
	let preview = $state('');
	let sampleName = $state('');
	let promptSaved = $state(false);
	let promptError = $state('');

	async function loadPrompt() {
		const data = await get(`/api/campaigns/${id}/prompt`);
		prompt = data.prompt;
		defaultPrompt = data.default_prompt;
		preview = data.preview;
		sampleName = data.sample_contact?.name || 'sample contact';
	}

	async function savePrompt() {
		promptError = '';
		try {
			await put(`/api/campaigns/${id}/prompt`, { prompt });
			await loadPrompt();
			promptSaved = true;
			setTimeout(() => (promptSaved = false), 2000);
		} catch (e: any) {
			promptError = e.message;
		}
	}

	function resetPrompt() {
		prompt = defaultPrompt;
	}

	onMount(loadPrompt);

	let running = $state(false);
	let done = $state(0);
	let total = $state(0);
	let kept = $state(0);
	let dropped = $state(0);
	let finished = $state(false);
	let error = $state('');
	let limit = $state<number | null>(null);

	async function startGenerate() {
		running = true;
		error = '';
		const token = await getToken();
		const params = new URLSearchParams();
		if (limit) params.set('limit', String(limit));
		const url = `${BASE}/api/campaigns/${id}/generate?${params}`;
		let res: Response;
		try {
			res = await fetch(url, {
				method: 'POST',
				headers: token ? { Authorization: `Bearer ${token}` } : {}
			});
		} catch (e: any) {
			error = `Could not reach API: ${e.message}`;
			running = false;
			return;
		}

		const reader = res.body!.getReader();
		const decoder = new TextDecoder();
		while (true) {
			const { value, done: streamDone } = await reader.read();
			if (streamDone) break;
			for (const line of decoder.decode(value).split('\n')) {
				if (!line.startsWith('data:')) continue;
				try {
					const event = JSON.parse(line.slice(5).trim());
					if (event.event === 'start') total = event.total;
					if (event.event === 'progress') {
						done = event.done;
						kept = event.kept ?? kept;
						dropped = event.dropped ?? dropped;
					}
					if (event.event === 'done') {
						kept = event.kept ?? kept;
						dropped = event.dropped ?? dropped;
						finished = true;
					}
				} catch {}
			}
		}
		running = false;
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card>
		<StepHeader
			step={3}
			title="Generate emails"
			description="Enriches verified contacts and generates personalized cold emails via Claude."
		/>

		{#if !running && !finished}
			<div class="mb-6 border border-neutral-200 rounded-lg p-4 bg-neutral-50">
				<p class="text-xs font-medium text-neutral-400 uppercase tracking-widest mb-2">
					Generation prompt
				</p>
				<p class="text-xs text-neutral-500 mb-3">
					This system prompt is sent to Claude for every contact in this campaign. Edit it to
					change tone and focus.
				</p>
				<textarea
					bind:value={prompt}
					rows="12"
					class="w-full font-mono text-xs leading-relaxed border border-neutral-200 rounded-lg p-3 bg-white text-neutral-800"
				></textarea>
				<div class="mt-2 flex items-center gap-3">
					<button
						onclick={savePrompt}
						class="px-4 py-1.5 bg-neutral-900 text-white rounded-lg text-xs font-medium"
					>
						Save prompt
					</button>
					<button
						onclick={resetPrompt}
						class="px-4 py-1.5 border border-neutral-200 text-neutral-600 rounded-lg text-xs"
					>
						Reset to default
					</button>
					{#if promptSaved}<span class="text-xs text-green-700">Saved</span>{/if}
					{#if promptError}<span class="text-xs text-red-500">{promptError}</span>{/if}
				</div>

				<p class="text-xs font-medium text-neutral-400 uppercase tracking-widest mt-5 mb-2">
					Full prompt preview — {sampleName}
				</p>
				<p class="text-xs text-neutral-500 mb-2">
					Exactly what gets sent, with this contact's variables filled in. During generation the
					bio is first rewritten into a short narrative by a summarizer.
				</p>
				<pre
					class="max-h-72 overflow-auto whitespace-pre-wrap font-mono text-xs leading-relaxed border border-neutral-200 rounded-lg p-3 bg-white text-neutral-700">{preview}</pre>
			</div>
		{/if}

		{#if !running && !finished}
			<div class="mb-5 flex items-center justify-between">
				<LimitInput bind:value={limit} placeholder="All verified" />
				<button
					onclick={startGenerate}
					class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium"
				>
					Generate emails
				</button>
			</div>
		{:else}
			<div class="space-y-4">
				<ProgressLine value={done} max={total || 1} label="emails generated" />
				<div class="flex gap-6 text-sm text-neutral-500">
					<span><span class="font-medium text-neutral-900">{done}</span> processed</span>
					<span><span class="font-medium text-green-700">{kept}</span> drafted</span>
					<span class="ml-auto text-neutral-400">{total} total</span>
				</div>
			</div>

			{#if finished}
				<div class="mt-6 pt-6 border-t border-neutral-100">
					<p class="text-sm text-neutral-500 mb-4">
						Done — <span class="font-medium text-green-700">{kept}</span> emails drafted.
					</p>
					<div class="flex justify-end">
						<button
							onclick={() => goto(`/campaigns/${id}/sample`)}
							class="px-5 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium"
						>
							Review sample →
						</button>
					</div>
				</div>
			{/if}
		{/if}

		{#if error}
			<p class="text-xs text-red-500 mt-3">{error}</p>
		{/if}
		<StepNav
			campaignId={id}
			prev={{ href: `/campaigns/${id}/verify`, label: '← Verify' }}
			next={{ href: `/campaigns/\${id}/sample`, label: 'Review sample' }}
		/>
	</Card>
</div>
