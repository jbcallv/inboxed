import { writable } from 'svelte/store';
import type { Session } from '@supabase/supabase-js';

export const session = writable<Session | null>(null);
export const currentCampaignId = writable<string | null>(null);
