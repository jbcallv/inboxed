import { getToken } from './supabase';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

async function headers(): Promise<HeadersInit> {
	const token = await getToken();
	return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function get(path: string) {
	const res = await fetch(`${BASE}${path}`, { headers: await headers() });
	if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
	return res.json();
}

export async function post(path: string, body?: unknown) {
	const res = await fetch(`${BASE}${path}`, {
		method: 'POST',
		headers: { ...(await headers()), 'Content-Type': 'application/json' },
		body: body !== undefined ? JSON.stringify(body) : undefined
	});
	if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
	return res.json();
}

export async function postForm(path: string, form: FormData) {
	const res = await fetch(`${BASE}${path}`, {
		method: 'POST',
		headers: await headers(),
		body: form
	});
	if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
	return res.json();
}

export function sseUrl(path: string) {
	return `${BASE}${path}`;
}
