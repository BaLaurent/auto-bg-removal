import { create } from "zustand";

import type { ModelInfo, PointDTO, PredictRequest, PredictResponse } from "../api";
import * as api from "../api";
import { decodeRLE, encodeRLE } from "../codec";
import { type Op, pushOp } from "./history";

export type Tool = "points" | "box" | "brush_add" | "brush_erase";
export type Status = "idle" | "uploading" | "predicting" | "switching" | "exporting";

interface State {
  // image
  image: HTMLImageElement | null;
  imageW: number;
  imageH: number;

  // session
  sessionId: string | null;
  status: Status;
  errorMessage: string | null;

  // mask layers — Uint8Array de longueur imageW * imageH (row-major)
  samMask: Uint8Array | null;
  userAdd: Uint8Array | null;
  userErase: Uint8Array | null;
  maskVersion: number; // bump pour notifier les hooks de rendu

  // points qui définissent la sélection courante (pour mode "points")
  points: PointDTO[];

  // tool / brush
  tool: Tool;
  brushSize: number;

  // models
  models: ModelInfo[];
  activeModel: string;

  // history
  history: Op[];
  historyIndex: number;

  // actions
  setTool: (t: Tool) => void;
  setBrushSize: (n: number) => void;
  upload: (file: File) => Promise<void>;
  reset: () => void;
  loadModels: () => Promise<void>;
  switchModel: (name: string) => Promise<void>;
  addPoint: (p: PointDTO) => Promise<void>;
  predictBox: (b: { x1: number; y1: number; x2: number; y2: number }) => Promise<void>;
  predictAuto: () => Promise<void>;
  applyStroke: (layer: "add" | "erase", before: Uint8Array, after: Uint8Array, bbox: [number, number, number, number]) => void;
  undo: () => void;
  redo: () => void;
  exportPng: () => Promise<void>;
}

function emptyMask(h: number, w: number): Uint8Array {
  return new Uint8Array(h * w);
}

function rleOrNull(mask: Uint8Array | null, h: number, w: number): string | null {
  if (!mask) return null;
  // exit early sur mask vide pour éviter encode coûteux
  for (let i = 0; i < mask.length; i++) if (mask[i]) return encodeRLE(mask, h, w);
  return null;
}

function applyRle(rle: string | null, h: number, w: number): Uint8Array {
  if (!rle) return emptyMask(h, w);
  return decodeRLE(rle, h, w);
}

function applyOp(state: State, op: Op, direction: "do" | "undo"): Partial<State> {
  const { imageH: h, imageW: w } = state;
  if (op.kind === "sam") {
    const rle = direction === "do" ? op.samAfterRle : op.samBeforeRle;
    const points = direction === "do" ? op.pointsAfter : op.pointsBefore;
    return {
      samMask: applyRle(rle, h, w),
      points: [...points],
      maskVersion: state.maskVersion + 1,
    };
  }
  // stroke
  const target = op.layer === "add" ? state.userAdd! : state.userErase!;
  const buffer = direction === "do" ? op.after : op.before;
  const next = new Uint8Array(target);
  const [x0, y0, bw, bh] = op.bbox;
  for (let yy = 0; yy < bh; yy++) {
    for (let xx = 0; xx < bw; xx++) {
      next[(y0 + yy) * w + (x0 + xx)] = buffer[yy * bw + xx];
    }
  }
  return op.layer === "add"
    ? { userAdd: next, maskVersion: state.maskVersion + 1 }
    : { userErase: next, maskVersion: state.maskVersion + 1 };
}

export const useEditor = create<State>((set, get) => ({
  image: null,
  imageW: 0,
  imageH: 0,
  sessionId: null,
  status: "idle",
  errorMessage: null,
  samMask: null,
  userAdd: null,
  userErase: null,
  maskVersion: 0,
  points: [],
  tool: "points",
  brushSize: 24,
  models: [],
  activeModel: "",
  history: [],
  historyIndex: 0,

  setTool: (t) => set({ tool: t }),
  setBrushSize: (n) => set({ brushSize: Math.max(2, Math.min(256, n)) }),

  reset: () =>
    set((s) => ({
      samMask: s.imageW ? emptyMask(s.imageH, s.imageW) : null,
      userAdd: s.imageW ? emptyMask(s.imageH, s.imageW) : null,
      userErase: s.imageW ? emptyMask(s.imageH, s.imageW) : null,
      points: [],
      history: [],
      historyIndex: 0,
      maskVersion: s.maskVersion + 1,
    })),

  upload: async (file) => {
    set({ status: "uploading", errorMessage: null });
    try {
      const created = await api.createSession(file);
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.src = url;
      await img.decode();
      set({
        sessionId: created.session_id,
        image: img,
        imageW: created.image.width,
        imageH: created.image.height,
        samMask: emptyMask(created.image.height, created.image.width),
        userAdd: emptyMask(created.image.height, created.image.width),
        userErase: emptyMask(created.image.height, created.image.width),
        points: [],
        history: [],
        historyIndex: 0,
        maskVersion: get().maskVersion + 1,
        activeModel: created.model,
        status: "idle",
      });
    } catch (e) {
      set({ status: "idle", errorMessage: errMsg(e) });
    }
  },

  loadModels: async () => {
    try {
      const r = await api.listModels();
      set({ models: r.available, activeModel: r.active });
    } catch (e) {
      set({ errorMessage: errMsg(e) });
    }
  },

  switchModel: async (name) => {
    set({ status: "switching", errorMessage: null });
    try {
      const r = await api.setActiveModel(name);
      set({ models: r.available, activeModel: r.active });
      const sid = get().sessionId;
      if (sid) await api.recomputeSession(sid);
      set({ status: "idle" });
    } catch (e) {
      set({ status: "idle", errorMessage: errMsg(e) });
    }
  },

  addPoint: async (p) => {
    const { sessionId, imageH: h, imageW: w, points, samMask, history, historyIndex } = get();
    if (!sessionId) return;
    const pointsBefore = [...points];
    const samBeforeRle = rleOrNull(samMask, h, w);
    const newPoints = [...points, p];
    set({ status: "predicting", points: newPoints });
    try {
      const body: PredictRequest = { mode: "points", points: newPoints };
      const resp: PredictResponse = await api.predict(sessionId, body);
      const newMask = decodeRLE(resp.mask.counts, resp.mask.size[0], resp.mask.size[1]);
      const op: Op = {
        kind: "sam",
        samBeforeRle,
        samAfterRle: rleOrNull(newMask, h, w),
        pointsBefore,
        pointsAfter: newPoints,
      };
      const { stack, index } = pushOp(history, historyIndex, op);
      set({
        samMask: newMask,
        history: stack,
        historyIndex: index,
        maskVersion: get().maskVersion + 1,
        status: "idle",
      });
    } catch (e) {
      set({ status: "idle", points: pointsBefore, errorMessage: errMsg(e) });
    }
  },

  predictBox: async (b) => {
    const { sessionId, imageH: h, imageW: w, samMask, points, history, historyIndex } = get();
    if (!sessionId) return;
    set({ status: "predicting" });
    const samBeforeRle = rleOrNull(samMask, h, w);
    const pointsBefore = [...points];
    try {
      const resp = await api.predict(sessionId, { mode: "box", box: b });
      const newMask = decodeRLE(resp.mask.counts, resp.mask.size[0], resp.mask.size[1]);
      const op: Op = {
        kind: "sam",
        samBeforeRle,
        samAfterRle: rleOrNull(newMask, h, w),
        pointsBefore,
        pointsAfter: [], // box reset les points
      };
      const { stack, index } = pushOp(history, historyIndex, op);
      set({
        samMask: newMask,
        points: [],
        history: stack,
        historyIndex: index,
        maskVersion: get().maskVersion + 1,
        status: "idle",
      });
    } catch (e) {
      set({ status: "idle", errorMessage: errMsg(e) });
    }
  },

  predictAuto: async () => {
    const { sessionId, imageH: h, imageW: w, samMask, points, history, historyIndex } = get();
    if (!sessionId) return;
    set({ status: "predicting" });
    const samBeforeRle = rleOrNull(samMask, h, w);
    const pointsBefore = [...points];
    try {
      const resp = await api.predict(sessionId, { mode: "auto" });
      const newMask = decodeRLE(resp.mask.counts, resp.mask.size[0], resp.mask.size[1]);
      const op: Op = {
        kind: "sam",
        samBeforeRle,
        samAfterRle: rleOrNull(newMask, h, w),
        pointsBefore,
        pointsAfter: [],
      };
      const { stack, index } = pushOp(history, historyIndex, op);
      set({
        samMask: newMask,
        points: [],
        history: stack,
        historyIndex: index,
        maskVersion: get().maskVersion + 1,
        status: "idle",
      });
    } catch (e) {
      set({ status: "idle", errorMessage: errMsg(e) });
    }
  },

  applyStroke: (layer, before, after, bbox) => {
    const { history, historyIndex } = get();
    const op: Op = { kind: "stroke", layer, bbox, before, after };
    const { stack, index } = pushOp(history, historyIndex, op);
    set({ history: stack, historyIndex: index });
  },

  undo: () => {
    const s = get();
    if (s.historyIndex === 0) return;
    const op = s.history[s.historyIndex - 1];
    const patch = applyOp(s, op, "undo");
    set({ ...patch, historyIndex: s.historyIndex - 1 });
  },

  redo: () => {
    const s = get();
    if (s.historyIndex >= s.history.length) return;
    const op = s.history[s.historyIndex];
    const patch = applyOp(s, op, "do");
    set({ ...patch, historyIndex: s.historyIndex + 1 });
  },

  exportPng: async () => {
    const { sessionId, samMask, userAdd, userErase, imageH: h, imageW: w } = get();
    if (!sessionId || !samMask || !userAdd || !userErase) return;
    set({ status: "exporting", errorMessage: null });
    try {
      const finalMask = composeFinal(samMask, userAdd, userErase);
      const counts = encodeRLE(finalMask, h, w);
      const blob = await api.exportPng(sessionId, { counts, size: [h, w] });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `cutout-${sessionId}.png`;
      link.click();
      URL.revokeObjectURL(link.href);
      set({ status: "idle" });
    } catch (e) {
      set({ status: "idle", errorMessage: errMsg(e) });
    }
  },
}));

export function composeFinal(samMask: Uint8Array, userAdd: Uint8Array, userErase: Uint8Array): Uint8Array {
  const out = new Uint8Array(samMask.length);
  for (let i = 0; i < samMask.length; i++) {
    out[i] = ((samMask[i] | userAdd[i]) & ~userErase[i]) & 1;
  }
  return out;
}

function errMsg(e: unknown): string {
  if (e instanceof api.ApiError) {
    const p = e.payload as { error?: string; detail?: string } | string | null;
    if (p && typeof p === "object") {
      if (p.detail) return p.detail;
      if (p.error) return p.error;
    }
    if (typeof p === "string" && p) return p;
    return `HTTP ${e.status}`;
  }
  if (e instanceof Error) return e.message;
  return String(e);
}
