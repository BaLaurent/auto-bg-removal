import { useEffect } from "react";

import { useEditor, type Tool } from "../state";

const TOOL_KEYS: Record<string, Tool> = {
  p: "points",
  b: "brush_add",
  e: "brush_erase",
  r: "box", // R for "rectangle"
};

const NUMBER_TO_TOOL: Tool[] = ["points", "box", "brush_add", "brush_erase"];

function isFromForm(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

export function useKeyboardShortcuts(): void {
  const undo = useEditor((s) => s.undo);
  const redo = useEditor((s) => s.redo);
  const setTool = useEditor((s) => s.setTool);
  const predictAuto = useEditor((s) => s.predictAuto);
  const setBrushSize = useEditor((s) => s.setBrushSize);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (isFromForm(e.target)) return;

      const meta = e.ctrlKey || e.metaKey;
      const key = e.key.toLowerCase();

      // Undo / Redo
      if (meta && key === "z" && !e.shiftKey) {
        e.preventDefault();
        undo();
        return;
      }
      if (meta && (key === "y" || (key === "z" && e.shiftKey))) {
        e.preventDefault();
        redo();
        return;
      }
      if (meta) return; // ignore autres combos meta

      // Lettres = sélecteur d'outil
      if (key in TOOL_KEYS) {
        e.preventDefault();
        setTool(TOOL_KEYS[key]);
        return;
      }

      // 1..4 = sélecteur d'outil par index
      if (key >= "1" && key <= "4") {
        const idx = Number(key) - 1;
        e.preventDefault();
        setTool(NUMBER_TO_TOOL[idx]);
        return;
      }

      // A = auto-segment (un coup)
      if (key === "a") {
        e.preventDefault();
        void predictAuto();
        return;
      }

      // [ ] = ajuster taille brush
      if (key === "[") {
        e.preventDefault();
        const cur = useEditor.getState().brushSize;
        setBrushSize(Math.max(2, Math.round(cur * 0.8)));
        return;
      }
      if (key === "]") {
        e.preventDefault();
        const cur = useEditor.getState().brushSize;
        setBrushSize(Math.min(256, Math.round(cur * 1.25)));
        return;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo, setTool, predictAuto, setBrushSize]);
}
