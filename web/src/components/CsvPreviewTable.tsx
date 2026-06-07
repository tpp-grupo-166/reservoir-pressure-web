import { useEffect, useState } from "react";

interface Props {
  file: File | null;
  maxRows?: number;
}

interface CsvData {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

export function CsvPreviewTable({ file, maxRows = 5 }: Props) {
  const [data, setData] = useState<CsvData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [displayRowCount, setDisplayRowCount] = useState(maxRows);

  useEffect(() => {
    if (!file) {
      setData(null);
      setError(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("El archivo no es un CSV");
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);

    let cancelled = false;
    file.text()
      .then((text) => {
        if (cancelled) return;

        const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
        
        if (lines.length === 0) {
          setError("El archivo está vacío");
          setData(null);
          setLoading(false);
          return;
        }

        const headers = parseCsvLine(lines[0]);
        const totalRows = lines.length - 1;
        
        const allRows = lines.slice(1).map((line) => parseCsvLine(line));

        setData({ headers, rows: allRows, totalRows });
        setLoading(false);
      })
      .catch((err) => {
        if (!cancelled) {
          setError("Error al leer el archivo");
          console.error(err);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [file]);

  useEffect(() => {
    setDisplayRowCount(maxRows);
  }, [file, maxRows]);

  if (!file) return null;
  if (loading) return <p className="csv-preview__loading">Cargando vista previa...</p>;
  if (error) return <p className="csv-preview__error">{error}</p>;
  if (!data) return null;

  const displayedRows = data.rows.slice(0, displayRowCount);

  return (
    <div className="csv-preview">
      <div className="csv-preview__header">
        <p className="csv-preview__title">Vista previa</p>
        <div className="csv-preview__controls">
          <label htmlFor="row-limit" className="csv-preview__label">Filas a mostrar:</label>
          <input
            id="row-limit"
            type="number"
            min="1"
            max={data.totalRows}
            value={displayRowCount}
            onChange={(e) => {
              const value = parseInt(e.target.value, 10);
              if (!isNaN(value) && value > 0) {
                setDisplayRowCount(value);
              }
            }}
            className="csv-preview__input"
          />
        </div>
      </div>
      <div className="csv-preview__scroll">
        <table className="csv-preview__table">
          <thead>
            <tr>
              {data.headers.map((header, index) => (
                <th key={index}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayedRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell || "-"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function parseCsvLine(line: string): string[] {
  return line.split(",").map((cell) => cell.trim());
}
