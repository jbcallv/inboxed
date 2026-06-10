<script lang="ts">
	interface Props {
		campaignId: string;
		prev?: { href: string; label: string } | null;
		next?: { href: string; label: string; disabled?: boolean } | null;
	}
	let { campaignId, prev = null, next = null }: Props = $props();
</script>

<div class="flex items-center justify-between mt-6 pt-4 border-t border-neutral-100">
	<div class="flex items-center gap-4">
		<a href="/campaigns/{campaignId}"
			class="text-sm text-neutral-400 hover:text-neutral-700 transition-colors">
			← Campaign hub
		</a>
		{#if prev}
			<a href={prev.href}
				class="text-sm text-neutral-400 hover:text-neutral-700 transition-colors">
				{prev.label}
			</a>
		{/if}
	</div>
	{#if next}
		<a href={next.href}
			class="px-4 py-2 bg-neutral-900 text-white rounded-lg text-sm font-medium
				{next.disabled ? 'opacity-40 pointer-events-none' : 'hover:bg-neutral-800'} transition-colors">
			{next.label} →
		</a>
	{/if}
</div>
