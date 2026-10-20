import { fetchJson } from "./client";
import type { SessionCreated, SessionState } from "./types";

export async function createSession(file: File): Promise<SessionCreated> {
  const fd = new FormData();
  fd.append("file", file);
  return fetchJson<SessionCreated>("/sessions", { method: "POST", body: fd });
}

export function getSessionState(id: string): Promise<SessionState> {
  return fetchJson<SessionState>(`/sessions/${id}`);
}

export function recomputeSession(id: string): Promise<SessionState> {
  return fetchJson<SessionState>(`/sessions/${id}/recompute`, { method: "POST" });
}

export async function deleteSession(id: string): Promise<void> {
  await fetch(`/api/sessions/${id}`, { method: "DELETE" });
}
