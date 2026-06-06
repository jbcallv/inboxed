<script lang="ts">
	let { onfile } = $props<{ onfile: (file: File) => void }>();
	let dragging = $state(false);
	let inputEl: HTMLInputElement;

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragging = false;
		const file = e.dataTransfer?.files?.[0];
		if (file) onfile(file);
	}

	function handleChange(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (file) onfile(file);
	}
</script>

<button
	type="button"
	class="w-full border-2 border-dashed border-neutral-200 rounded-lg p-12 text-center cursor-pointer transition-colors
		{dragging ? 'border-neutral-400 bg-neutral-50' : 'hover:border-neutral-300'}"
	ondragover={(e) => { e.preventDefault(); dragging = true; }}
	ondragleave={() => { dragging = false; }}
	ondrop={handleDrop}
	onclick={() => inputEl.click()}
>
	<p class="text-sm text-neutral-400">Drop a CSV or XLSX file here, or click to browse</p>
	<input
		bind:this={inputEl}
		type="file"
		accept=".csv,.xlsx"
		class="hidden"
		onchange={handleChange}
	/>
</button>
