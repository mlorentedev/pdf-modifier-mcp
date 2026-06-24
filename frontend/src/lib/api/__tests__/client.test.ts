import { describe, it, expect, vi, beforeEach } from 'vitest';
import { uploadPdf, getStructure, replaceText, downloadPdf, deleteSession } from '../client';

describe('API Client', () => {
	beforeEach(() => {
		vi.resetAllMocks();
	});

	describe('uploadPdf', () => {
		it('uploads a PDF file successfully', async () => {
			const mockResponse = { session_id: 'abc123' };
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			} as Response);

			const file = new File(['%PDF-1.4'], 'test.pdf', { type: 'application/pdf' });
			const result = await uploadPdf(file);

			expect(result).toEqual(mockResponse);
			expect(fetch).toHaveBeenCalledWith('/api/pdf/upload', expect.objectContaining({
				method: 'POST'
			}));
		});

		it('throws error on upload failure', async () => {
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: false,
				json: () => Promise.resolve({ detail: 'Invalid PDF' })
			} as Response);

			const file = new File(['invalid'], 'test.txt', { type: 'text/plain' });
			await expect(uploadPdf(file)).rejects.toThrow('Invalid PDF');
		});
	});

	describe('getStructure', () => {
		it('fetches PDF structure', async () => {
			const mockStructure = {
				success: true,
				total_pages: 1,
				pages: []
			};
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockStructure)
			} as Response);

			const result = await getStructure('abc123');
			expect(result).toEqual(mockStructure);
		});
	});

	describe('replaceText', () => {
		it('sends replacements to API', async () => {
			const mockResult = {
				success: true,
				replacements_made: 2,
				pages_modified: 1,
				warnings: []
			};
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResult)
			} as Response);

			const result = await replaceText('abc123', [
				{ old: 'foo', new: 'bar' },
				{ old: 'baz', new: 'qux' }
			]);

			expect(result).toEqual(mockResult);
			expect(fetch).toHaveBeenCalledWith('/api/pdf/abc123/replace', expect.objectContaining({
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			}));
		});
	});

	describe('downloadPdf', () => {
		it('downloads modified PDF', async () => {
			const mockBlob = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true,
				blob: () => Promise.resolve(mockBlob)
			} as Response);

			const result = await downloadPdf('abc123');
			expect(result).toBe(mockBlob);
		});
	});

	describe('deleteSession', () => {
		it('deletes session', async () => {
			vi.spyOn(global, 'fetch').mockResolvedValue({
				ok: true
			} as Response);

			await deleteSession('abc123');
			expect(fetch).toHaveBeenCalledWith('/api/pdf/abc123', { method: 'DELETE' });
		});
	});
});
