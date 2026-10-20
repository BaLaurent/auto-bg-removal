import { fetchJson } from "./client";
import type { PredictRequest, PredictResponse } from "./types";

export function predict(sessionId: string, body: PredictRequest): Promise<PredictResponse> {
  return fetchJson<PredictResponse>(`/sessions/${sessionId}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
