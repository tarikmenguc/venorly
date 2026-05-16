import { supabase } from './supabase';

/**
 * Backend API base URL'ini döner.
 * - Tarayıcıda: '' (relative path → Vercel proxy üzerinden /api/...)
 * - Sunucuda (SSR): NEXT_PUBLIC_API_URL veya localhost fallback
 */
export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
}

/**
 * Auth token'lı fetch wrapper.
 * Supabase session varsa Authorization header ekler.
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token;

  const url = `${getApiUrl()}${path}`;

  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
}
