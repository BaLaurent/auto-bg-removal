import { useEditor } from "../state";

export function StatusBar() {
  const sessionId = useEditor((s) => s.sessionId);
  const activeModel = useEditor((s) => s.activeModel);
  const status = useEditor((s) => s.status);
  const tool = useEditor((s) => s.tool);
  const historyIndex = useEditor((s) => s.historyIndex);
  const historyLen = useEditor((s) => s.history.length);
  const imageW = useEditor((s) => s.imageW);
  const imageH = useEditor((s) => s.imageH);

  return (
    <div className="status-bar">
      <span><strong>Modèle</strong>: {activeModel || "—"}</span>
      <span>
        <strong>Image</strong>: {imageW && imageH ? `${imageW}×${imageH}` : "—"}
      </span>
      <span>
        <strong>Session</strong>: {sessionId ? sessionId.slice(0, 8) : "—"}
      </span>
      <span>
        <strong>Outil</strong>: {tool}
      </span>
      <span>
        <strong>Ops</strong>: {historyIndex}/{historyLen}
      </span>
      <span className={`tag ${status === "idle" ? "ok" : "busy"}`}>{status}</span>
      <span className="hint">P = points · R = box · B = brush+ · E = brush− · A = auto · [ ] = taille pinceau · Ctrl+Z / Ctrl+Shift+Z</span>
    </div>
  );
}
