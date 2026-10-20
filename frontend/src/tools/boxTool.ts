import { useEditor } from "../state";
import type { ImgPointerEvent, ToolHandlers } from "./types";

export interface BoxToolDeps {
  setDraggingBox: (box: { x1: number; y1: number; x2: number; y2: number } | null) => void;
}

export function createBoxTool(deps: BoxToolDeps): ToolHandlers {
  let start: { x: number; y: number } | null = null;

  return {
    onPointerDown(e: ImgPointerEvent) {
      if (!e.pt || !e.primary) return;
      start = e.pt;
      deps.setDraggingBox({ x1: e.pt.x, y1: e.pt.y, x2: e.pt.x, y2: e.pt.y });
    },
    onPointerMove(e: ImgPointerEvent) {
      if (!start || !e.pt) return;
      deps.setDraggingBox({ x1: start.x, y1: start.y, x2: e.pt.x, y2: e.pt.y });
    },
    onPointerUp(e: ImgPointerEvent) {
      if (!start) return;
      const end = e.pt ?? start;
      const x1 = Math.min(start.x, end.x);
      const y1 = Math.min(start.y, end.y);
      const x2 = Math.max(start.x, end.x);
      const y2 = Math.max(start.y, end.y);
      start = null;
      deps.setDraggingBox(null);
      if (x2 - x1 < 2 || y2 - y1 < 2) return; // ignore micro-drag
      void useEditor.getState().predictBox({ x1, y1, x2, y2 });
    },
  };
}
