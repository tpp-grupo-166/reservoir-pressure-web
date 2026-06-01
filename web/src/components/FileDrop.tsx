import { useRef, useState } from "react";

interface Props {
  label: string;
  accept?: string;
  file: File | null;
  onSelect: (file: File) => void;
}

/** Zona de arrastrar-soltar / elegir archivo. */
export function FileDrop({ label, accept = ".csv", file, onSelect }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  return (
    <div
      className={`filedrop ${dragging ? "filedrop--active" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f) onSelect(f);
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onSelect(f);
        }}
      />
      <p>{file ? `✓ ${file.name}` : `Arrastrá ${label} o hacé clic para elegir`}</p>
    </div>
  );
}
