<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { get, put } from '$lib/api';
	import Card from '$lib/components/Card.svelte';

	const id = $derived($page.params.id);
	let address = $state('');
	let saving = $state(false);
	let saved = $state(false);

	onMount(async () => {
		const campaign = await get(`/api/campaigns/${id}`).catch(() => null);
		address = campaign?.physical_address ?? '';
	});

	async function save() {
		saving = true;
		saved = false;
		await put(`/api/campaigns/${id}/settings`, { physical_address: address });
		saving = false;
		saved = true;
	}
</script>

<div class="max-w-2xl mx-auto py-16 px-4">
	<Card>
		<div class="mb-6">
			<h2 class="text-xl font-semibold text-neutral-900">Compliance settings</h2>
			<p class="mt-1 text-sm text-neutral-500">
				US law (CAN-SPAM) requires a physical postal address in every commercial email. It's
				appended in small text under the unsubscribe link on every email this campaign sends.
			</p>
		</div>
		<hr class="border-neutral-100 mb-6" />

		<label class="block text-xs text-neutral-500 mb-1" for="address">Physical mailing address</label>
		<textarea
			id="address"
			bind:value={address}
			rows="2"
			placeholder="123 Main St, Suite 100, Austin, TX 78701"
			class="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400"
			oninput={() => (saved = false)}
		></textarea>

		<button onclick={save} disabled={saving || !address.trim()}
			class="mt-4 px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium disabled:opacity-50">
			{saving ? 'Saving…' : 'Save'}
		</button>
		{#if saved}
			<span class="ml-3 text-xs text-green-600">Saved</span>
		{/if}
	</Card>
</div>
