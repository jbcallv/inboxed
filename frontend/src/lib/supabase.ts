import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export async function getSession() {
	const { data } = await supabase.auth.getSession();
	return data.session;
}

export async function getToken(): Promise<string | null> {
	const session = await getSession();
	return session?.access_token ?? null;
}
