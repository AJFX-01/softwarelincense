// Client for the FastAPI backend (licensewise/api.py). In dev, Vite proxies /api to :8000.

import { useEffect, useState } from "react";
import type { License, Result } from "./types";

export type JobStatus = "queued" | "running" | "done" | "failed";

export interface JobSummary {
  id: string;
  status: JobStatus;
  created_at: string;
  description: string | null;
  manifest_name: string | null;
  top_pick: string | null;
  claims_verified: number;
  claims_total: number;
  error: string | null;
  reused?: boolean;
}

export interface Job {
  id: string;
  status: JobStatus;
  step: string | null;
  step_detail: string | null;
  queued_ahead: number;
  created_at: string;
  error: string | null;
  input: { description: string | null; manifest: { name: string; content: string } | null; verify: boolean };
  result: Result | null;
}

export interface SampleInfo {
  name: string;
  title: string;
  about: string;
}

export class ApiError extends Error {}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, init);
  } catch {
    throw new ApiError("Can't reach the backend. Start it with: .venv/bin/uvicorn licensewise.api:app --port 8000");
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    // FastAPI validation errors are a list; show the first message
    const message = Array.isArray(detail) ? detail[0]?.msg : detail;
    throw new ApiError(message ?? `Backend error (${response.status}).`);
  }
  return body as T;
}

export const api = {
  health: () => call<{ status: string; model: string }>("/health"),
  licenses: () => call<License[]>("/licenses"),
  history: () => call<JobSummary[]>("/recommendations"),
  samples: () => call<SampleInfo[]>("/samples"),
  sample: (name: string) => call<unknown>(`/samples/${encodeURIComponent(name)}`),
  job: (id: string) => call<Job>(`/recommendations/${id}`),
  recommend: (description: string, manifest: { name: string; content: string } | null) =>
    call<JobSummary>("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: description || null, manifest }),
    }),
};

/** null while checking, then whether /api/health answered. Re-checks every 30 s. */
export function useBackendOnline(): boolean | null {
  const [online, setOnline] = useState<boolean | null>(null);
  useEffect(() => {
    const check = () => api.health().then(() => setOnline(true), () => setOnline(false));
    check();
    const timer = setInterval(check, 30_000);
    return () => clearInterval(timer);
  }, []);
  return online;
}
