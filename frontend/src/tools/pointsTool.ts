import { useEditor } from "../state";
import type { ImgPointerEvent, ToolHandlers } from "./types";

export function createPointsTool(): ToolHandlers {
  return {
    onPointerDown(e: ImgPointerEvent) {
      if (!e.pt || !e.primary) return;
      const label: 0 | 1 = e.shiftKey || e.altKey ? 0 : 1;
      void useEditor.getState().addPoint({ x: e.pt.x, y: e.pt.y, label });
    },
  };
}
