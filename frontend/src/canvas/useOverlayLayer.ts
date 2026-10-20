import { useEffect, type RefObject } from "react";

import type { PointDTO } from "../api";
import { computeMapping, type Viewport } from "./coords";

export interface OverlayHints {
  points: PointDTO[];
  /** Drag de box en cours, en image-coords. */
  draggingBox: { x1: number; y1: number; x2: number; y2: number } | null;
  /** Position du curseur en image-coords (pour preview brush). */
  cursor: { x: number; y: number } | null;
  /** Outil actif et taille pinceau (pour preview cercle). */
  tool: string;
  brushSize: number;
}

export function useOverlayLayer(
  canvasRef: RefObject<HTMLCanvasElement | null>,
  viewport: Viewport,
  hints: OverlayHints,
) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!viewport.imageW) return;
    const m = computeMapping(viewport);

    // points
    for (const p of hints.points) {
      const cx = p.x * m.scale + m.offsetX;
      const cy = p.y * m.scale + m.offsetY;
      ctx.beginPath();
      ctx.arc(cx, cy, 6, 0, Math.PI * 2);
      ctx.fillStyle = p.label === 1 ? "#22d36a" : "#f87171";
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#0e0e10";
      ctx.stroke();
    }

    // box drag
    if (hints.draggingBox) {
      const b = hints.draggingBox;
      const x1 = Math.min(b.x1, b.x2) * m.scale + m.offsetX;
      const y1 = Math.min(b.y1, b.y2) * m.scale + m.offsetY;
      const x2 = Math.max(b.x1, b.x2) * m.scale + m.offsetX;
      const y2 = Math.max(b.y1, b.y2) * m.scale + m.offsetY;
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = "#f5d142";
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      ctx.setLineDash([]);
    }

    // brush cursor preview
    if (hints.cursor && (hints.tool === "brush_add" || hints.tool === "brush_erase")) {
      const cx = hints.cursor.x * m.scale + m.offsetX;
      const cy = hints.cursor.y * m.scale + m.offsetY;
      const r = (hints.brushSize / 2) * m.scale;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = hints.tool === "brush_add" ? "#22d36a" : "#f87171";
      ctx.stroke();
    }
  }, [
    canvasRef,
    viewport.domW,
    viewport.domH,
    viewport.imageW,
    viewport.imageH,
    hints.points,
    hints.draggingBox,
    hints.cursor,
    hints.tool,
    hints.brushSize,
  ]);
}
