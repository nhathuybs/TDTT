// Shared API base URL helper.
//
// `VITE_API_BASE_URL` may be configured as either:
// - backend root (e.g. https://...run.app)
// - backend api prefix (e.g. https://...run.app/api)
//
// This file normalizes it so the rest of the app can always use `API_URL`
// (which includes `/api` exactly once).

const RAW_API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  "https://smart-travel-api-85676926926.asia-southeast1.run.app";

function trimTrailingSlashes(url: string): string {
  return (url || "").trim().replace(/\/+$/, "");
}

function buildApiUrl(url: string): string {
  const trimmed = trimTrailingSlashes(url);
  if (!trimmed) return "";
  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
}

export const API_URL = buildApiUrl(RAW_API_BASE_URL);

