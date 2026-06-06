<script lang="ts">
	import { session } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	$effect(() => {
		if ($session) goto('/campaigns');
	});

	async function login() {
		loading = true;
		error = '';
		const { error: err } = await supabase.auth.signInWithPassword({ email, password });
		if (err) error = err.message;
		loading = false;
	}
</script>

<div class="flex items-center justify-center min-h-screen">
	<div class="w-full max-w-sm">
		<h1 class="text-2xl font-semibold text-neutral-900 mb-1">Inboxed</h1>
		<p class="text-sm text-neutral-400 mb-8">Verified cold email, autonomously.</p>

		<form onsubmit={(e) => { e.preventDefault(); login(); }} class="space-y-4">
			<div>
				<label class="block text-xs text-neutral-500 mb-1" for="email">Email</label>
				<input
					id="email"
					type="email"
					bind:value={email}
					required
					class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400"
				/>
			</div>
			<div>
				<label class="block text-xs text-neutral-500 mb-1" for="password">Password</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					required
					class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400"
				/>
			</div>
			{#if error}
				<p class="text-xs text-red-500">{error}</p>
			{/if}
			<button
				type="submit"
				disabled={loading}
				class="w-full bg-neutral-900 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50"
			>
				{loading ? 'Signing in…' : 'Sign in'}
			</button>
		</form>
	</div>
</div>
