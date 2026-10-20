import { useEffect, type RefObject } from "react";

import { computeMapping, type Viewport } from "./coords";

const MASK_COLOR: [number, number, number, number] = [0, 200, 255, 110];

export function useMaskLayer(
  canvasRef: RefObject<HTMLCanvasElement | null>,
  samMask: Uint8Array | null,
  userAdd: Uint8Array | null,
  userErase: Uint8Array | null,
  viewport: Viewport,
  maskVersion: number,
) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!samMask || !userAdd || !userErase || !viewport.imageW) return;

    const { imageW: w, imageH: h } = viewport;
    const offCanvas =
      typeof OffscreenCanvas !== "undefined"
        ? new OffscreenCanvas(w, h)
        : Object.assign(document.createElement("canvas"), { width: w, height: h });
    const offCtx = offCanvas.getContext("2d");
    if (!offCtx) return;
    const imgData = offCtx.createImageData(w, h);
    const buf = imgData.data;
    const [r, g, b, a] = MASK_COLOR;
    for (let i = 0, n = w * h; i < n; i++) {
      const v = (samMask[i] | userAdd[i]) & ~userErase[i] & 1;
      if (v) {
        const o = i << 2;
        buf[o] = r;
        buf[o + 1] = g;
        buf[o + 2] = b;
        buf[o + 3] = a;
      }
    }
    offCtx.putImageData(imgData, 0, 0);

    const m = computeMapping(viewport);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(
      offCanvas as CanvasImageSource,
      m.offsetX,
      m.offsetY,
      w * m.scale,
      h * m.scale,
    );
  }, [
    canvasRef,
    samMask,
    userAdd,
    userErase,
    viewport.domW,
    viewport.domH,
    viewport.imageW,
    viewport.imageH,
    maskVersion,
  ]);
}
