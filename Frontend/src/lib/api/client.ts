/**
 * Thin fetch wrapper for the AgentHound backend.
 *
 * The base URL defaults to the local dev backend (`http://localhost:8000`) and
 * can be overridden with `NEXT_PUBLIC_AGENTHOUND_API_URL` for other
 * environments. Non-2xx responses are turned into an {@link ApiError} carrying
 * the backend's error envelope code (spec section 13) when present.
 */

import type { ApiErrorEnvelope } from "./types";

const DEFAULT_BASE_URL = "http://localhost:8000";

export function apiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_AGENTHOUND_API_URL ?? DEFAULT_BASE_URL;
  return configured.replace(/\/+$/, "");
}

/** An error raised for any non-2xx backend response. `code` is the backend
 * error envelope code (e.g. `INVALID_INPUT`) when the body followed the
 * envelope shape, otherwise a synthetic `HTTP_<status>`. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: Record<string, unknown>;

  constructor(code: string, message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = undefined;
  }
  const envelope = body as Partial<ApiErrorEnvelope> | undefined;
  if (envelope?.error?.code) {
    return new ApiError(envelope.error.code, envelope.error.message, res.status, envelope.error.details);
  }
  return new ApiError(`HTTP_${res.status}`, res.statusText || "Request failed", res.status);
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl()}${path}`, init);
  } catch (cause) {
    // Network-level failure (backend down, CORS, DNS): no HTTP status.
    throw new ApiError(
      "NETWORK_ERROR",
      cause instanceof Error ? cause.message : "Could not reach the backend.",
      0,
    );
  }
  if (!res.ok) {
    throw await toApiError(res);
  }
  return (await res.json()) as T;
}
