import { useEffect, useRef, useState } from "react";

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
  // Resumen "N filas, M columnas" del CSV cargado (no aplica a otros formatos, ej. TOML).
  const [summary, setSummary] = useState<string | null>(null);

  useEffect(() => {
    if (!file || !file.name.toLowerCase().endsWith(".csv")) {
      setSummary(null);
      return;
    }
    let cancelled = false;
    file.text().then((text) => {
      if (cancelled) return;
      const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
      const rows = Math.max(0, lines.length - 1); // descuenta el header
      const cols = lines.length ? lines[0].split(",").length : 0;
      setSummary(`${rows} filas, ${cols} columnas`);
    }).catch(() => { if (!cancelled) setSummary(null); });
    return () => { cancelled = true; };
  }, [file]);

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
      {file && summary && <p className="filedrop__summary">{summary}</p>}
    </div>
  );
}
