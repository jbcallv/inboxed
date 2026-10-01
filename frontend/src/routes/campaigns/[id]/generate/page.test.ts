import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';

const CAMPAIGN_ID = '7f3c2a10-0000-4000-8000-000000000001';

const mockGet = vi.fn().mockResolvedValue({
	prompt: 'Write a short email',
	default_prompt: 'Write a short email',
	preview: '',
	sample_contact: null
});
vi.mock('$lib/api', () => ({ get: mockGet, put: vi.fn() }));
vi.mock('$lib/supabase', () => ({ getToken: vi.fn() }));
vi.mock('$app/navigation', () => ({ goto: vi.fn() }));
vi.mock('$app/stores', () => ({
	page: {
		subscribe(run: (value: { params: { id: string } }) => void) {
			run({ params: { id: CAMPAIGN_ID } });
			return () => {};
		}
	}
}));

const { default: Page } = await import('./+page.svelte');

describe('generate page', () => {
	it('links to the sample step with the real campaign id', async () => {
		render(Page);

		await waitFor(() => expect(mockGet).toHaveBeenCalledWith(`/api/campaigns/${CAMPAIGN_ID}/prompt`));
		const sampleLink = screen.getByRole('link', { name: /review sample/i });
		expect(sampleLink.getAttribute('href')).toBe(`/campaigns/${CAMPAIGN_ID}/sample`);
	});
});
