import { useEditor } from "../state";

export function ErrorBanner() {
  const errorMessage = useEditor((s) => s.errorMessage);
  if (!errorMessage) return null;

  function dismiss() {
    useEditor.setState({ errorMessage: null });
  }

  return (
    <div className="error-banner" role="alert">
      <span className="error-icon" aria-hidden="true">!</span>
      <span className="error-text">{errorMessage}</span>
      <button className="error-dismiss" onClick={dismiss} aria-label="Fermer">
        ×
      </button>
    </div>
  );
}
