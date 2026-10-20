import { useRef } from "react";

import { useEditor } from "../state";

export function UploadArea() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const upload = useEditor((s) => s.upload);
  const status = useEditor((s) => s.status);

  return (
    <div className="upload-area">
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        style={{ display: "none" }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) void upload(f);
          e.target.value = "";
        }}
      />
      <button
        className="btn primary"
        disabled={status === "uploading"}
        onClick={() => inputRef.current?.click()}
      >
        {status === "uploading" ? "Upload…" : "Charger une image"}
      </button>
    </div>
  );
}
