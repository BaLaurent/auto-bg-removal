import { fetchJson } from "./client";
import type { ModelsResponse } from "./types";

export function listModels(): Promise<ModelsResponse> {
  return fetchJson<ModelsResponse>("/models");
}

export function setActiveModel(name: string): Promise<ModelsResponse> {
  return fetchJson<ModelsResponse>("/models/active", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}
