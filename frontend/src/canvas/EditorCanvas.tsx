import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { useEditor } from "../state";
import { createToolHandlers } from "../tools";
import { domToImage, type Viewport } from "./coords";
import { useImageLayer } from "./useImageLayer";
import { useMaskLayer } from "./useMaskLayer";
import { useOverlayLayer } from "./useOverlayLayer";

export function EditorCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const imgCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const maskCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const image = useEditor((s) => s.image);
  const imageW = useEditor((s) => s.imageW);
  const imageH = useEditor((s) => s.imageH);
  const samMask = useEditor((s) => s.samMask);
  const userAdd = useEditor((s) => s.userAdd);
  const userErase = useEditor((s) => s.userErase);
  const maskVersion = useEditor((s) => s.maskVersion);
  const points = useEditor((s) => s.points);
  const tool = useEditor((s) => s.tool);
  const brushSize = useEditor((s) => s.brushSize);

  const [domSize, setDomSize] = useState({ w: 0, h: 0 });
  const [draggingBox, setDraggingBox] = useState<
    { x1: number; y1: number; x2: number; y2: number } | null
  >(null);
  const [cursor, setCursor] = useState<{ x: number; y: number } | null>(null);

  // mesure du conteneur — ResizeObserver + fallback raf au mount pour les cas
  // où la grille parent n'est pas encore layoutée au moment du useLayoutEffect.
  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    let raf = 0;
    const measure = () => {
      const r = el.getBoundingClientRect();
      const w = Math.floor(r.width);
      const h = Math.floor(r.height);
      if (w > 0 && h > 0) {
        setDomSize((prev) => (prev.w === w && prev.h === h ? prev : { w, h }));
      }
    };
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    measure();
    raf = requestAnimationFrame(measure);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  // sync canvas pixel size avec DPR. On ne touche au canvas que si on a une
  // taille DOM connue ; sinon le c.width=0 le rend invisible et le CSS inset:0
  // ne peut plus le faire grandir (style.width override).
  useEffect(() => {
    if (domSize.w === 0 || domSize.h === 0) return;
    const dpr = window.devicePixelRatio || 1;
    for (const ref of [imgCanvasRef, maskCanvasRef, overlayCanvasRef]) {
      const c = ref.current;
      if (!c) continue;
      c.width = Math.floor(domSize.w * dpr);
      c.height = Math.floor(domSize.h * dpr);
      const ctx = c.getContext("2d");
      if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
  }, [domSize.w, domSize.h]);

  const viewport: Viewport = useMemo(
    () => ({ domW: domSize.w, domH: domSize.h, imageW, imageH }),
    [domSize.w, domSize.h, imageW, imageH],
  );

  useImageLayer(imgCanvasRef, image, viewport);
  useMaskLayer(maskCanvasRef, samMask, userAdd, userErase, viewport, maskVersion);
  useOverlayLayer(overlayCanvasRef, viewport, {
    points,
    draggingBox,
    cursor,
    tool,
    brushSize,
  });

  const handlers = useMemo(
    () => createToolHandlers(tool, { setDraggingBox }),
    [tool],
  );

  function buildEvent(e: React.PointerEvent<HTMLDivElement>) {
    const el = containerRef.current;
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const pt = domToImage(viewport, e.clientX - r.left, e.clientY - r.top);
    return {
      pt,
      shiftKey: e.shiftKey,
      altKey: e.altKey,
      primary: (e.buttons & 1) === 1 || e.type === "pointerdown",
    };
  }

  return (
    <div
      ref={containerRef}
      className="editor-canvas"
      onPointerDown={(e) => {
        if (!image) return;
        (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
        const ev = buildEvent(e);
        if (ev) handlers.onPointerDown?.(ev);
      }}
      onPointerMove={(e) => {
        if (!image) return;
        const ev = buildEvent(e);
        if (!ev) return;
        setCursor(ev.pt);
        handlers.onPointerMove?.(ev);
      }}
      onPointerUp={(e) => {
        if (!image) return;
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
        const ev = buildEvent(e);
        if (ev) handlers.onPointerUp?.(ev);
      }}
      onPointerLeave={() => setCursor(null)}
    >
      <canvas ref={imgCanvasRef} className="layer" />
      <canvas ref={maskCanvasRef} className="layer" />
      <canvas ref={overlayCanvasRef} className="layer overlay" />
      {!image && <div className="empty-hint">Charge une image pour commencer.</div>}
    </div>
  );
}
