<script lang="ts">
	import './layout.css';
	import { supabase } from '$lib/supabase';
	import { session } from '$lib/stores';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		supabase.auth.getSession().then(({ data }) => session.set(data.session));
		supabase.auth.onAuthStateChange((_, s) => session.set(s));
	});

	const onCampaignPage = $derived($page.url.pathname.startsWith('/campaigns'));
	const onAuthPage = $derived($page.url.pathname === '/');
</script>

<div class="min-h-screen bg-neutral-50 font-sans">
	{#if !onAuthPage}
		<header class="border-b border-neutral-200 bg-white">
			<div class="max-w-2xl mx-auto px-4 h-12 flex items-center gap-4">
				<a href="/campaigns" class="text-sm font-semibold text-neutral-900 tracking-tight">Inboxed</a>
				{#if onCampaignPage}
					<span class="text-neutral-300 text-xs">—</span>
					<a href="/campaigns" class="text-xs text-neutral-400 hover:text-neutral-700 transition-colors">All campaigns</a>
				{/if}
			</div>
		</header>
	{/if}
	{@render children()}
</div>
