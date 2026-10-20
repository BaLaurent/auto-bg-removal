import { useEditor } from "../state";
import { drawDisk, drawSegment, emptyBBox, isEmptyBBox, snapshotBBox } from "./painting";
import type { ImgPointerEvent, ToolHandlers } from "./types";

export function createBrushTool(layer: "add" | "erase"): ToolHandlers {
  let beforeSnapshot: Uint8Array | null = null;
  let lastPt: { x: number; y: number } | null = null;
  const dirty = emptyBBox();

  function bumpVersion() {
    useEditor.setState({ maskVersion: useEditor.getState().maskVersion + 1 });
  }

  return {
    onPointerDown(e: ImgPointerEvent) {
      if (!e.pt || !e.primary) return;
      const s = useEditor.getState();
      const target = layer === "add" ? s.userAdd : s.userErase;
      if (!target) return;
      beforeSnapshot = new Uint8Array(target);
      dirty.x0 = Infinity;
      dirty.y0 = Infinity;
      dirty.x1 = -Infinity;
      dirty.y1 = -Infinity;
      const r = s.brushSize / 2;
      drawDisk(target, s.imageW, s.imageH, e.pt.x, e.pt.y, r, 1, dirty);
      lastPt = e.pt;
      bumpVersion();
    },
    onPointerMove(e: ImgPointerEvent) {
      if (!beforeSnapshot || !lastPt || !e.primary) return;
      const s = useEditor.getState();
      const target = layer === "add" ? s.userAdd : s.userErase;
      if (!target || !e.pt) return;
      const r = s.brushSize / 2;
      drawSegment(target, s.imageW, s.imageH, lastPt.x, lastPt.y, e.pt.x, e.pt.y, r, 1, dirty);
      lastPt = e.pt;
      bumpVersion();
    },
    onPointerUp(_e: ImgPointerEvent) {
      if (!beforeSnapshot) return;
      const s = useEditor.getState();
      const after = layer === "add" ? s.userAdd : s.userErase;
      if (!after || isEmptyBBox(dirty)) {
        beforeSnapshot = null;
        lastPt = null;
        return;
      }
      const snap = snapshotBBox(beforeSnapshot, after, s.imageW, dirty);
      s.applyStroke(layer, snap.before, snap.after, snap.bbox);
      beforeSnapshot = null;
      lastPt = null;
    },
  };
}
