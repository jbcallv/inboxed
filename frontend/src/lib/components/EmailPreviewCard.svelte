<script lang="ts">
	let { email } = $props<{
		email: {
			id: number;
			subject: string;
			body: string;
			contact?: { first_name?: string; last_name?: string; company_name?: string };
		};
	}>();
</script>

<div class="border border-neutral-200 rounded-lg bg-white p-5">
	<p class="text-xs text-neutral-400 mb-2">
		{email.contact?.first_name ?? ''} {email.contact?.last_name ?? ''}
		{#if email.contact?.company_name}· {email.contact.company_name}{/if}
	</p>
	<p class="font-medium text-sm text-neutral-900 mb-3">{email.subject}</p>
	<p class="text-sm text-neutral-600 whitespace-pre-line leading-relaxed">{email.body}</p>
</div>
