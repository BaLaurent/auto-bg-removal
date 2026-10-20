import { fetchBlob } from "./client";
import type { MaskRLEDTO } from "./types";

export function exportPng(sessionId: string, mask: MaskRLEDTO): Promise<Blob> {
  return fetchBlob(`/sessions/${sessionId}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mask }),
  });
}
