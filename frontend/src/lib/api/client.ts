const API_BASE = '/api';

export interface UploadResponse {
	session_id: string;
}

export interface StructureResponse {
	success: boolean;
	file_path: string;
	total_pages: number;
	pages: PageStructure[];
}

export interface PageStructure {
	page: number;
	width: number;
	height: number;
	text_elements: TextElement[];
}

export interface TextElement {
	text: string;
	bbox: [number, number, number, number];
	origin: [number, number];
	font: string;
	size: number;
	color: number;
}

export interface ReplaceResponse {
	success: boolean;
	replacements_made: number;
	pages_modified: number;
	warnings: string[];
}

export interface Replacement {
	old: string;
	new: string;
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
	const formData = new FormData();
	formData.append('file', file);

	const response = await fetch(`${API_BASE}/pdf/upload`, {
		method: 'POST',
		body: formData
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Upload failed');
	}

	return response.json();
}

export async function getStructure(sessionId: string): Promise<StructureResponse> {
	const response = await fetch(`${API_BASE}/pdf/${sessionId}/structure`);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to get structure');
	}

	return response.json();
}

export async function replaceText(
	sessionId: string,
	replacements: Replacement[],
	useRegex = false
): Promise<ReplaceResponse> {
	const replacementsMap: Record<string, string> = {};
	for (const r of replacements) {
		replacementsMap[r.old] = r.new;
	}

	const response = await fetch(`${API_BASE}/pdf/${sessionId}/replace`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			replacements: replacementsMap,
			use_regex: useRegex
		})
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Replacement failed');
	}

	return response.json();
}

export async function downloadPdf(sessionId: string): Promise<Blob> {
	const response = await fetch(`${API_BASE}/pdf/${sessionId}/download`);

	if (!response.ok) {
		throw new Error('Download failed');
	}

	return response.blob();
}

export async function deleteSession(sessionId: string): Promise<void> {
	const response = await fetch(`${API_BASE}/pdf/${sessionId}`, {
		method: 'DELETE'
	});

	if (!response.ok) {
		throw new Error('Delete failed');
	}
}
