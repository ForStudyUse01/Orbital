import type { Envelope } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
let accessTokenProvider: (() => Promise<string | null>) | null = null;

export function configureAccessTokenProvider(provider: () => Promise<string | null>): void {
  accessTokenProvider = provider;
}

async function headers(includeContentType = false): Promise<Record<string, string>> {
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  return {
    Accept: "application/json",
    ...(includeContentType ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function apiGet<T>(path: string): Promise<Envelope<T>> {
  const response = await fetch(`${API_BASE}${path}`, { headers: await headers() });
  if (!response.ok) throw new ApiError(response.status, await response.text());
  return response.json() as Promise<Envelope<T>>;
}

export async function apiSend<T>(path: string, method: "POST" | "PUT" | "DELETE", body?: unknown): Promise<Envelope<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: await headers(true),
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status, await response.text());
  return response.status === 204 ? ({ data: null } as Envelope<T>) : response.json() as Promise<Envelope<T>>;
}

export function exportUrl(path: string): string { return `${API_BASE}${path}`; }
