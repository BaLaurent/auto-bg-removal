import { useEditor } from "../state";

export function ExportButton() {
  const exportPng = useEditor((s) => s.exportPng);
  const sessionId = useEditor((s) => s.sessionId);
  const status = useEditor((s) => s.status);
  const samMask = useEditor((s) => s.samMask);

  const disabled = !sessionId || status !== "idle" || !samMask;

  return (
    <button className="btn primary" disabled={disabled} onClick={() => exportPng()}>
      {status === "exporting" ? "Export…" : "Export PNG"}
    </button>
  );
}
