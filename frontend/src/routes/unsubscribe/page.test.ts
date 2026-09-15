import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';

const mockPost = vi.fn();
vi.mock('$lib/api', () => ({ post: mockPost }));

let currentQuery = '';
vi.mock('$app/stores', () => ({
	page: {
		subscribe(run: (value: { url: URL }) => void) {
			run({ url: new URL(`http://localhost/unsubscribe${currentQuery}`) });
			return () => {};
		}
	}
}));

const { default: Page } = await import('./+page.svelte');

describe('unsubscribe page', () => {
	beforeEach(() => {
		mockPost.mockReset();
		currentQuery = '';
	});

	it('shows a message when the link is missing query params', () => {
		render(Page);
		expect(screen.getByText(/missing information/i)).toBeTruthy();
	});

	it('unsubscribes on confirm and shows success', async () => {
		currentQuery = '?email=alice%40acme.com&campaign=campaign-uuid';
		mockPost.mockResolvedValue({ status: 'unsubscribed' });
		render(Page);

		expect(screen.getByText('alice@acme.com')).toBeTruthy();
		await fireEvent.click(screen.getByRole('button', { name: /unsubscribe me/i }));

		await waitFor(() => expect(screen.getByText(/you're unsubscribed/i)).toBeTruthy());
		expect(mockPost).toHaveBeenCalledWith('/api/unsubscribe', {
			email: 'alice@acme.com',
			campaign_id: 'campaign-uuid'
		});
	});

	it('shows an error and lets the user retry on failure', async () => {
		currentQuery = '?email=alice%40acme.com&campaign=campaign-uuid';
		mockPost.mockRejectedValue(new Error('POST /api/unsubscribe → 404'));
		render(Page);

		await fireEvent.click(screen.getByRole('button', { name: /unsubscribe me/i }));

		await waitFor(() => expect(screen.getByText(/couldn't process/i)).toBeTruthy());
		expect(screen.getByRole('button', { name: /try again/i })).toBeTruthy();
	});
});
