export type PredictMode = "points" | "box" | "auto";

export interface PointDTO {
  x: number;
  y: number;
  label: 0 | 1;
}

export interface BoxDTO {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface MaskRLEDTO {
  counts: string; // base64
  size: [number, number]; // [h, w]
}

export interface PredictRequest {
  mode: PredictMode;
  points?: PointDTO[];
  box?: BoxDTO;
}

export interface PredictResponse {
  mask: MaskRLEDTO;
  score: number;
  model: string;
}

export interface SessionCreated {
  session_id: string;
  image: { width: number; height: number };
  embedding_ready: boolean;
  model: string;
}

export interface SessionState {
  session_id: string;
  embedding_ready: boolean;
  model: string;
}

export interface ModelInfo {
  name: string;
  loaded: boolean;
  size_mb: number | null;
}

export interface ModelsResponse {
  active: string;
  available: ModelInfo[];
}
