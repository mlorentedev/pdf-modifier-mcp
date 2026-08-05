<script lang="ts">
	import { onMount, tick } from 'svelte';
	import * as pdfjsLib from 'pdfjs-dist';
	import { getHighlightRects, type HighlightViewport } from '$lib/utils/highlight';

	pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

	let { sessionId, highlightText = '' }: { sessionId: string; highlightText?: string } = $props();

	let canvas: HTMLCanvasElement;
	let currentPage = $state(1);
	let totalPages = $state(0);
	let pdfDoc: pdfjsLib.PDFDocumentProxy | null = null;
	let loading = $state(true);
	let error = $state<string | null>(null);
	let scale = $state(1.5);
	let pageInput = $state('1');
	let rendering = $state(false);
	let renderToken = 0;

	const MIN_SCALE = 0.25;
	const MAX_SCALE = 4;
	const ZOOM_STEP = 1.25;

	onMount(async () => {
		try {
			const response = await fetch(`/api/pdf/${sessionId}/download`);
			const buffer = await response.arrayBuffer();
			const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(buffer) });
			pdfDoc = await loadingTask.promise;
			totalPages = pdfDoc.numPages;
			pageInput = String(currentPage);
			loading = false;
			// Wait for DOM to update (canvas appears after loading=false)
			await tick();
			renderPage(currentPage);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load PDF';
			loading = false;
		}
	});

	// Re-render (with highlights) whenever the highlight term changes.
	$effect(() => {
		const term = highlightText;
		if (!pdfDoc || !canvas || !term.trim()) return;
		renderPage(currentPage);
	});

	async function renderPage(pageNum: number) {
		if (!pdfDoc || !canvas) return;

		const token = ++renderToken;
		rendering = true;

		try {
			const page = await pdfDoc.getPage(pageNum);
			const viewport = page.getViewport({ scale });

			const context = canvas.getContext('2d');
			if (!context) return;

			canvas.height = viewport.height;
			canvas.width = viewport.width;

			await page.render({
				canvasContext: context,
				viewport
			}).promise;

			// If a newer render was requested meanwhile, don't overlay stale highlights
			if (token !== renderToken) return;
			// Highlights are best-effort; never let a failure blank the rendered page
			drawHighlights(page, viewport).catch((e: unknown) => {
				console.error('PDF highlight error:', e);
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to render page';
		} finally {
			if (token === renderToken) rendering = false;
		}
	}

	async function drawHighlights(page: pdfjsLib.PDFPageProxy, viewport: pdfjsLib.PageViewport) {
		const term = highlightText.trim();
		if (!term) return;

		const textContent = await page.getTextContent();
		const context = canvas.getContext('2d');
		if (!context) return;

		const textItems = textContent.items.filter(
			(i): i is { str: string; transform: number[]; width: number; height: number } => 'str' in i
		);
		const vp: HighlightViewport = { scale: viewport.scale, transform: viewport.transform };
		const rects = getHighlightRects(term, textItems, vp);

		context.fillStyle = 'rgba(255, 235, 59, 0.35)';
		for (const r of rects) {
			context.fillRect(r.x, r.y, r.width, r.height);
		}
	}

	function zoom(dir: 1 | -1) {
		const next = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale * (dir > 0 ? ZOOM_STEP : 1 / ZOOM_STEP)));
		if (next === scale) return;
		scale = next;
		renderPage(currentPage);
	}

	function fitToWidth() {
		const container = document.querySelector('.pdf-scroll');
		if (!container || !pdfDoc) return;
		const cw = container.clientWidth - 24;
		pdfDoc.getPage(currentPage).then(page => {
			const base = page.getViewport({ scale: 1 });
			scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, cw / base.width));
			renderPage(currentPage);
		});
	}

	function prevPage() {
		if (currentPage > 1) {
			currentPage--;
			pageInput = String(currentPage);
			renderPage(currentPage);
		}
	}

	function nextPage() {
		if (currentPage < totalPages) {
			currentPage++;
			pageInput = String(currentPage);
			renderPage(currentPage);
		}
	}

	function jumpToPage() {
		const n = parseInt(pageInput, 10);
		if (isNaN(n) || n < 1 || n > totalPages) {
			pageInput = String(currentPage);
			return;
		}
		currentPage = n;
		renderPage(currentPage);
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
		<!-- Toolbar: page nav, zoom, page jump -->
		<div class="flex items-center justify-between mb-4">
			<div class="flex items-center gap-2">
				<button
					onclick={prevPage}
					disabled={currentPage <= 1 || rendering}
					class="px-3 py-1 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600 text-sm"
				>←</button>
				<span class="text-gray-400 text-sm">
					Page
					<input
						type="number"
						min="1" max={totalPages}
						bind:value={pageInput}
						onchange={jumpToPage}
						class="w-12 bg-gray-700 rounded px-2 py-1 text-sm text-center"
					/>
					/ {totalPages}
				</span>
				<button
					onclick={nextPage}
					disabled={currentPage >= totalPages || rendering}
					class="px-3 py-1 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600 text-sm"
				>→</button>
			</div>
			<div class="flex items-center gap-1">
				<button
					onclick={() => zoom(-1)}
					disabled={scale <= MIN_SCALE || rendering}
					class="px-2 py-1 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600 text-sm"
					title="Zoom out"
				>🔍−</button>
				<span class="text-gray-400 text-xs w-12 text-center">{Math.round(scale * 100)}%</span>
				<button
					onclick={() => zoom(1)}
					disabled={scale >= MAX_SCALE || rendering}
					class="px-2 py-1 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600 text-sm"
					title="Zoom in"
				>🔍+</button>
				<button
					onclick={fitToWidth}
					class="px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-xs ml-1"
					title="Fit to width"
				>Fit</button>
			</div>
		</div>

		<div class="overflow-auto max-h-[600px] flex justify-center bg-gray-950 rounded p-2 pdf-scroll">
			<canvas
				bind:this={canvas}
				class="border border-gray-600 max-w-full h-auto"
				style="max-width:100%;"
			></canvas>
		</div>

		{#if highlightText}
			<div class="mt-3 text-sm text-gray-400">
				Highlighting: <span class="text-yellow-400">"{highlightText}"</span>
			</div>
		{/if}
	{/if}
</div>