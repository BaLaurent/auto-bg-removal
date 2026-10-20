import { useEffect } from "react";

import { useEditor } from "../state";

export function ModelSelector() {
  const models = useEditor((s) => s.models);
  const activeModel = useEditor((s) => s.activeModel);
  const status = useEditor((s) => s.status);
  const loadModels = useEditor((s) => s.loadModels);
  const switchModel = useEditor((s) => s.switchModel);

  useEffect(() => {
    void loadModels();
  }, [loadModels]);

  return (
    <div className="model-selector">
      <label>Modèle</label>
      <select
        value={activeModel || ""}
        disabled={status !== "idle"}
        onChange={(e) => switchModel(e.target.value)}
      >
        {models.map((m) => (
          <option key={m.name} value={m.name}>
            {m.name}
            {m.size_mb ? ` (${m.size_mb} MB)` : ""}
            {m.loaded ? "  ●" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
