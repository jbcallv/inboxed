<script lang="ts">
	import './layout.css';
	import { supabase } from '$lib/supabase';
	import { session } from '$lib/stores';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		supabase.auth.getSession().then(({ data }) => session.set(data.session));
		supabase.auth.onAuthStateChange((_, s) => session.set(s));
	});
</script>

<div class="min-h-screen bg-neutral-50 font-sans">
	{@render children()}
</div>
