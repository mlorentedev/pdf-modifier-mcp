<script lang="ts">
	import { uploadPdf, getStructure, replaceText, downloadPdf, type StructureResponse, type Replacement } from '$lib/api/client';
	import PdfPreview from '$lib/components/PdfPreview.svelte';
	import Toast from '$lib/components/Toast.svelte';

	// State
	let sessionId = $state<string | null>(null);
	let structure = $state<StructureResponse | null>(null);
	let replacements = $state<Replacement[]>([{ old: '', new: '' }]);
	let uploading = $state(false);
	let processing = $state(false);
	let error = $state<string | null>(null);
	let dragOver = $state(false);
	let uploadKey = $state(0);
	let highlightText = $state('');
	let toasts = $state<Array<{ id: number; message: string; type: 'success' | 'error' | 'info' }>>([]);
	let searchQuery = $state('');
	let history = $state<Array<{ replacements: Replacement[] }>>([]);
	let historyIndex = $state(-1);

	// Constants
	const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

	// Toast management
	let toastId = 0;
	function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
		toasts = [...toasts, { id: ++toastId, message, type }];
	}
	function removeToast(id: number) {
		toasts = toasts.filter(t => t.id !== id);
	}

	// History management
	function saveToHistory() {
		history = history.slice(0, historyIndex + 1);
		history = [...history, { replacements: structuredClone(replacements) }];
		historyIndex = history.length - 1;
	}
	function undo() {
		if (historyIndex > 0) {
			historyIndex--;
			replacements = structuredClone(history[historyIndex].replacements);
		}
	}
	function redo() {
		if (historyIndex < history.length - 1) {
			historyIndex++;
			replacements = structuredClone(history[historyIndex].replacements);
		}
	}

	// Validation
	function validateFile(file: File): string | null {
		if (file.type !== 'application/pdf') return 'Only PDF files are supported';
		if (file.size > MAX_FILE_SIZE) return `File too large (max ${MAX_FILE_SIZE / 1024 / 1024}MB)`;
		return null;
	}

	// Upload
	async function handleDrop(event: DragEvent) {
		event.preventDefault();
		dragOver = false;
		const files = event.dataTransfer?.files;
		if (!files || files.length === 0) return;
		await handleUpload(files[0]);
	}

	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) handleUpload(file);
	}

	async function handleUpload(file: File) {
		const validationError = validateFile(file);
		if (validationError) {
			showToast(validationError, 'error');
			return;
		}

		uploading = true;
		error = null;

		try {
			const result = await uploadPdf(file);
			sessionId = result.session_id;
			structure = await getStructure(sessionId);
			uploadKey++;
			saveToHistory();
			showToast('PDF uploaded successfully', 'success');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Upload failed';
			showToast(error, 'error');
		} finally {
			uploading = false;
		}
	}

	// Replacements
	function addReplacement() {
		replacements = [...replacements, { old: '', new: '' }];
		saveToHistory();
	}

	function removeReplacement(index: number) {
		replacements = replacements.filter((_, i) => i !== index);
		saveToHistory();
	}

	function prefillFromElement(text: string) {
		replacements = [...replacements, { old: text, new: '' }];
		highlightText = text;
		saveToHistory();
		showToast(`Added "${text}" as replacement target`, 'info');
	}

	function updateReplacement(index: number, field: 'old' | 'new', value: string) {
		replacements = replacements.map((r, i) => i === index ? { ...r, [field]: value } : r);
	}

	// Apply replacements
	async function handleReplace() {
		if (!sessionId) return;

		const validReplacements = replacements.filter(r => r.old && r.new);
		if (validReplacements.length === 0) {
			showToast('Add at least one replacement', 'error');
			return;
		}

		processing = true;
		error = null;

		try {
			const result = await replaceText(sessionId, validReplacements);
			uploadKey++;
			showToast(`Applied ${result.replacements_made} replacements`, 'success');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Replacement failed';
			showToast(error, 'error');
		} finally {
			processing = false;
		}
	}

	// Download
	async function handleDownload() {
		if (!sessionId) return;

		try {
			const blob = await downloadPdf(sessionId);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = 'modified.pdf';
			a.click();
			URL.revokeObjectURL(url);
			showToast('Download started', 'success');
		} catch (e) {
			showToast('Download failed', 'error');
		}
	}

	// Search
	let filteredElements = $derived(
		structure?.pages.flatMap(p => p.elements).filter(e =>
			!searchQuery || e.text.toLowerCase().includes(searchQuery.toLowerCase())
		) ?? []
	);

	// Drag handlers
	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		dragOver = true;
	}
	function handleDragLeave() { dragOver = false; }

	// Reset
	function reset() {
		sessionId = null;
		structure = null;
		replacements = [{ old: '', new: '' }];
		error = null;
		history = [];
		historyIndex = -1;
		uploadKey++;
	}

	// Keyboard shortcuts
	function handleKeydown(e: KeyboardEvent) {
		if (e.ctrlKey || e.metaKey) {
			if (e.key === 'z' && !e.shiftKey) { e.preventDefault(); undo(); }
			if (e.key === 'z' && e.shiftKey) { e.preventDefault(); redo(); }
			if (e.key === 'y') { e.preventDefault(); redo(); }
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#each toasts as toast (toast.id)}
	<Toast message={toast.message} type={toast.type} onclose={() => removeToast(toast.id)} />
{/each}

<div class="min-h-screen bg-gray-900 text-white p-6">
	<div class="flex items-center justify-between mb-6">
		<h1 class="text-3xl font-bold">PDF Modifier</h1>
		<div class="flex gap-2">
			{#if sessionId}
				<button onclick={undo} disabled={historyIndex <= 0}
					class="px-3 py-2 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600 text-sm"
					title="Ctrl+Z">↩ Undo</button>
				<button onclick={redo} disabled={historyIndex >= history.length - 1}
					class="px-3 py-2 bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-600 text-sm"
					title="Ctrl+Shift+Z">↪ Redo</button>
				<button onclick={reset}
					class="px-3 py-2 bg-gray-700 rounded hover:bg-gray-600 text-sm">New PDF</button>
			{/if}
		</div>
	</div>

	{#if !sessionId}
		<div
			role="button" tabindex="0"
			class="border-2 border-dashed rounded-lg p-16 text-center cursor-pointer transition-colors"
			class:border-blue-500={dragOver}
			class:border-gray-600={!dragOver}
			class:bg-gray-800={!dragOver}
			class:bg-gray-700={dragOver}
			ondrop={handleDrop} ondragover={handleDragOver} ondragleave={handleDragLeave}
		>
			{#if uploading}
				<div class="flex flex-col items-center gap-3">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
					<p class="text-xl text-gray-300">Uploading...</p>
				</div>
			{:else}
				<p class="text-xl text-gray-400 mb-2">Drag & drop a PDF here</p>
				<p class="text-gray-500">or click to select (max 100MB)</p>
				<input type="file" accept=".pdf" class="hidden" onchange={handleFileSelect} />
			{/if}
		</div>
	{:else}
		<div class="grid grid-cols-12 gap-4">
			<!-- Structure (left) -->
			<div class="col-span-3 bg-gray-800 rounded-lg p-4">
				<h2 class="text-lg font-semibold mb-3">Elements</h2>
				<input
					type="text" placeholder="Search..."
					bind:value={searchQuery}
					class="w-full bg-gray-700 rounded px-3 py-2 text-sm mb-3"
				/>
				<div class="max-h-[600px] overflow-y-auto space-y-1">
					{#each filteredElements as element}
						<button
							onclick={() => prefillFromElement(element.text)}
							class="w-full text-left bg-gray-700 p-2 rounded text-sm hover:bg-gray-600 transition-colors"
							class:ring-2={highlightText === element.text}
							class:ring-yellow-500={highlightText === element.text}
						>
							<div class="text-gray-200 truncate">{element.text}</div>
							<div class="text-gray-500 text-xs">{element.font} {element.size}pt</div>
						</button>
					{/each}
				</div>
			</div>

			<!-- PDF Preview (center) -->
			<div class="col-span-5">
				{#key uploadKey}
					<PdfPreview {sessionId} {highlightText} />
				{/key}
			</div>

			<!-- Replacements (right) -->
			<div class="col-span-4 bg-gray-800 rounded-lg p-4">
				<h2 class="text-lg font-semibold mb-3">Replacements</h2>
				<div class="space-y-2 max-h-[400px] overflow-y-auto">
					{#each replacements as replacement, i}
						<div class="flex gap-2">
							<input type="text" placeholder="Old text" value={replacement.old}
								oninput={(e) => updateReplacement(i, 'old', e.currentTarget.value)}
								class="flex-1 bg-gray-700 rounded px-3 py-2 text-sm" />
							<input type="text" placeholder="New text" value={replacement.new}
								oninput={(e) => updateReplacement(i, 'new', e.currentTarget.value)}
								class="flex-1 bg-gray-700 rounded px-3 py-2 text-sm" />
							<button onclick={() => removeReplacement(i)}
								class="px-2 py-2 bg-red-600/80 rounded hover:bg-red-500 text-sm">×</button>
						</div>
					{/each}
				</div>
				<button onclick={addReplacement}
					class="w-full mt-3 py-2 border border-gray-600 rounded hover:bg-gray-700 text-sm">+ Add</button>

				<div class="mt-4 space-y-2">
					<button onclick={handleReplace} disabled={processing}
						class="w-full py-3 bg-blue-600 rounded font-semibold hover:bg-blue-500 disabled:opacity-50">
						{processing ? 'Applying...' : 'Apply Replacements'}
					</button>
					<button onclick={handleDownload}
						class="w-full py-3 bg-green-600 rounded font-semibold hover:bg-green-500">
						Download PDF
					</button>
				</div>

				<div class="mt-4 text-sm text-gray-500">
					<p>{replacements.filter(r => r.old).length} replacements configured</p>
					<p class="text-xs mt-1">Click elements to add • Ctrl+Z/Y undo/redo</p>
				</div>
			</div>
		</div>
	{/if}
</div>
