import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock supabase getToken before importing api
vi.mock('./supabase', () => ({ getToken: vi.fn().mockResolvedValue('test-jwt') }));
// Mock import.meta.env
vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

const { get, post, postForm } = await import('./api');

describe('get', () => {
	beforeEach(() => vi.stubGlobal('fetch', vi.fn()));

	it('sends Authorization header with token', async () => {
		const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
		vi.stubGlobal('fetch', mockFetch);

		await get('/api/campaigns');

		const [url, opts] = mockFetch.mock.calls[0];
		expect(url).toBe('http://localhost:8000/api/campaigns');
		expect((opts.headers as Record<string, string>).Authorization).toBe('Bearer test-jwt');
	});

	it('throws on non-ok response', async () => {
		vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }));
		await expect(get('/api/campaigns')).rejects.toThrow('GET /api/campaigns → 401');
	});
});

describe('post', () => {
	it('sends JSON body with content-type header', async () => {
		const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: '1' }) });
		vi.stubGlobal('fetch', mockFetch);

		await post('/api/campaigns', { name: 'test' });

		const [, opts] = mockFetch.mock.calls[0];
		expect(opts.method).toBe('POST');
		expect((opts.headers as Record<string, string>)['Content-Type']).toBe('application/json');
		expect(JSON.parse(opts.body)).toEqual({ name: 'test' });
	});

	it('sends POST with no body when body is undefined', async () => {
		const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
		vi.stubGlobal('fetch', mockFetch);

		await post('/api/campaigns/abc/pause');

		const [, opts] = mockFetch.mock.calls[0];
		expect(opts.body).toBeUndefined();
	});

	it('throws on non-ok response', async () => {
		vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));
		await expect(post('/api/campaigns/bad')).rejects.toThrow('POST /api/campaigns/bad → 404');
	});
});

describe('postForm', () => {
	it('does not set Content-Type (let browser set multipart boundary)', async () => {
		const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ imported: 5 }) });
		vi.stubGlobal('fetch', mockFetch);

		const form = new FormData();
		form.append('file', new Blob(['csv data']), 'contacts.csv');
		await postForm('/api/campaigns/abc/upload', form);

		const [, opts] = mockFetch.mock.calls[0];
		expect(opts.method).toBe('POST');
		expect((opts.headers as Record<string, string>)['Content-Type']).toBeUndefined();
	});
});
