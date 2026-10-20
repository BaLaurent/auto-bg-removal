import { useEffect, type RefObject } from "react";

import { computeMapping, type Viewport } from "./coords";

export function useImageLayer(
  canvasRef: RefObject<HTMLCanvasElement | null>,
  image: HTMLImageElement | null,
  viewport: Viewport,
) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!image || !viewport.imageW) return;
    const m = computeMapping(viewport);
    ctx.drawImage(
      image,
      m.offsetX,
      m.offsetY,
      viewport.imageW * m.scale,
      viewport.imageH * m.scale,
    );
  }, [canvasRef, image, viewport.domW, viewport.domH, viewport.imageW, viewport.imageH]);
}
