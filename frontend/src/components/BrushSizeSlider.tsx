import { useEditor } from "../state";

export function BrushSizeSlider() {
  const tool = useEditor((s) => s.tool);
  const size = useEditor((s) => s.brushSize);
  const setSize = useEditor((s) => s.setBrushSize);

  if (tool !== "brush_add" && tool !== "brush_erase") return null;

  return (
    <div className="brush-slider">
      <label>Pinceau</label>
      <input
        type="range"
        min={2}
        max={256}
        value={size}
        onChange={(e) => setSize(Number(e.target.value))}
      />
      <span>{size}px</span>
    </div>
  );
}
