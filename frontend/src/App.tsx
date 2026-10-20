import { EditorCanvas } from "./canvas";
import { BrushSizeSlider } from "./components/BrushSizeSlider";
import { ErrorBanner } from "./components/ErrorBanner";
import { ExportButton } from "./components/ExportButton";
import { LoadingOverlay } from "./components/LoadingOverlay";
import { ModelSelector } from "./components/ModelSelector";
import { StatusBar } from "./components/StatusBar";
import { Toolbar } from "./components/Toolbar";
import { UploadArea } from "./components/UploadArea";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";

export default function App() {
  useKeyboardShortcuts();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Auto BG Removal</h1>
        <div className="header-actions">
          <ModelSelector />
          <UploadArea />
          <ExportButton />
        </div>
      </header>
      <Toolbar />
      <BrushSizeSlider />
      <ErrorBanner />
      <main className="editor">
        <EditorCanvas />
        <LoadingOverlay />
      </main>
      <StatusBar />
    </div>
  );
}
