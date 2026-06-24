<script lang="ts">
	import { onMount } from 'svelte';
	import * as pdfjsLib from 'pdfjs-dist';

	pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

	let { sessionId, highlightText = '' }: { sessionId: string; highlightText?: string } = $props();

	let canvas: HTMLCanvasElement;
	let currentPage = $state(1);
	let totalPages = $state(0);
	let pdfDoc: pdfjsLib.PDFDocumentProxy | null = null;
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			const url = `/api/pdf/${sessionId}/download`;
			const loadingTask = pdfjsLib.getDocument(url);
			pdfDoc = await loadingTask.promise;
			totalPages = pdfDoc.numPages;
			await renderPage(currentPage);
			loading = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load PDF';
			loading = false;
		}
	});

	async function renderPage(pageNum: number) {
		if (!pdfDoc || !canvas) return;

		try {
			const page = await pdfDoc.getPage(pageNum);
			const scale = 1.5;
			const viewport = page.getViewport({ scale });

			const context = canvas.getContext('2d');
			if (!context) return;

			canvas.height = viewport.height;
			canvas.width = viewport.width;

			await page.render({
				canvasContext: context,
				viewport
			}).promise;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to render page';
		}
	}

	function prevPage() {
		if (currentPage > 1) {
			currentPage--;
			renderPage(currentPage);
		}
	}

	function nextPage() {
		if (currentPage < totalPages) {
			currentPage++;
			renderPage(currentPage);
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'ArrowLeft') prevPage();
		if (e.key === 'ArrowRight') nextPage();
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="bg-gray-800 rounded-lg p-4">
	<h2 class="text-xl font-semibold mb-4">PDF Preview</h2>

	{#if loading}
		<div class="flex items-center justify-center h-64">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
			<span class="ml-3 text-gray-400">Loading PDF...</span>
		</div>
	{:else if error}
		<div class="p-4 bg-red-900/50 rounded text-red-400">{error}</div>
	{:else}
		<div class="flex items-center justify-between mb-4">
			<button
				onclick={prevPage}
				disabled={currentPage <= 1}
				class="px-3 py-1 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600"
			>
				← Prev
			</button>
			<span class="text-gray-400">Page {currentPage} / {totalPages}</span>
			<button
				onclick={nextPage}
				disabled={currentPage >= totalPages}
				class="px-3 py-1 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600"
			>
				Next →
			</button>
		</div>

		<div class="overflow-auto max-h-[600px] flex justify-center bg-gray-950 rounded p-2">
			<canvas bind:this={canvas} class="border border-gray-600"></canvas>
		</div>

		{#if highlightText}
			<div class="mt-3 text-sm text-gray-400">
				Highlighting: <span class="text-yellow-400">"{highlightText}"</span>
			</div>
		{/if}
	{/if}
</div>
