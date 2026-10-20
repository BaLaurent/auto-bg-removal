import { useEditor } from "../state";

const LABELS: Record<string, string> = {
  uploading: "Upload de l'image…",
  predicting: "Segmentation…",
  switching: "Chargement du modèle…",
  exporting: "Export PNG…",
};

export function LoadingOverlay() {
  const status = useEditor((s) => s.status);
  if (status === "idle") return null;
  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <span>{LABELS[status] ?? status}</span>
    </div>
  );
}
