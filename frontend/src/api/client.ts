const BASE = "/api";

export class ApiError extends Error {
  constructor(public status: number, public payload: unknown) {
    super(`HTTP ${status}`);
  }
}

/** Lit le body d'une réponse en erreur en une seule passe : on récupère le
 * texte brut, puis on tente de le parser en JSON. Si on tente .json() puis
 * .text() en fallback, le 2e read échoue avec « Body has already been consumed ».
 */
async function readErrorBody(r: Response): Promise<unknown> {
  const txt = await r.text();
  if (!txt) return null;
  try {
    return JSON.parse(txt);
  } catch {
    return txt;
  }
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, init);
  if (!r.ok) throw new ApiError(r.status, await readErrorBody(r));
  return (await r.json()) as T;
}

export async function fetchBlob(path: string, init?: RequestInit): Promise<Blob> {
  const r = await fetch(`${BASE}${path}`, init);
  if (!r.ok) throw new ApiError(r.status, await readErrorBody(r));
  return r.blob();
}
