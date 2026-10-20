import { useEditor, type Tool } from "../state";

const TOOLS: Array<{ id: Tool; label: string; hint: string }> = [
  { id: "points", label: "Points", hint: "Clic = inclure  ·  Shift+clic = exclure" },
  { id: "box", label: "Box", hint: "Drag pour entourer le sujet" },
  { id: "brush_add", label: "Brush +", hint: "Pinceau qui ajoute au masque" },
  { id: "brush_erase", label: "Brush −", hint: "Pinceau qui retire du masque" },
];

export function Toolbar() {
  const tool = useEditor((s) => s.tool);
  const setTool = useEditor((s) => s.setTool);
  const predictAuto = useEditor((s) => s.predictAuto);
  const reset = useEditor((s) => s.reset);
  const undo = useEditor((s) => s.undo);
  const redo = useEditor((s) => s.redo);
  const sessionId = useEditor((s) => s.sessionId);
  const status = useEditor((s) => s.status);
  const historyIndex = useEditor((s) => s.historyIndex);
  const historyLen = useEditor((s) => s.history.length);

  const disabled = !sessionId || status !== "idle";

  return (
    <div className="toolbar">
      <div className="tool-group">
        {TOOLS.map((t) => (
          <button
            key={t.id}
            className={`btn ${tool === t.id ? "active" : ""}`}
            disabled={!sessionId}
            title={t.hint}
            onClick={() => setTool(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="tool-group">
        <button className="btn" disabled={disabled} onClick={() => predictAuto()}>
          Auto-segment
        </button>
        <button className="btn" disabled={disabled || historyIndex === 0} onClick={undo}>
          ↶ Undo
        </button>
        <button
          className="btn"
          disabled={disabled || historyIndex >= historyLen}
          onClick={redo}
        >
          ↷ Redo
        </button>
        <button className="btn danger" disabled={disabled} onClick={reset}>
          Reset
        </button>
      </div>
    </div>
  );
}
