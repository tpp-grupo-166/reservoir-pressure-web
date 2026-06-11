import type { Explainability, ModelInfo } from "../types";

interface Props {
  explainability: Explainability;
  modelInfo: ModelInfo;
}

/** Sección de explicabilidad: el diferencial del proyecto. */
export function ExplainPanel({ explainability, modelInfo }: Props) {
  const m = modelInfo.metricas_validacion;
  return (
    <div className="explain">
      {explainability.advertencias.length > 0 && (
        <div className="explain__warnings">
          {explainability.advertencias.map((w, i) => (
            <p key={i}>⚠ {w}</p>
          ))}
        </div>
      )}

      <details>
        <summary>Qué tan confiable es</summary>
        <p>
          R² medio {m.R2_medio.toFixed(2)} ± {m.R2_std.toFixed(2)} · MAE esperado ≈ {m.MAE_psi.toFixed(0)} psi
        </p>
        <p className="explain__note">{modelInfo.nota}</p>
      </details>

      <details>
        <summary>Qué features construimos y por qué</summary>
        <ul>
          {explainability.features_construidos.map((f) => (
            <li key={f.nombre}>
              <strong>{f.nombre}</strong> — {f.descripcion} <em>{f.fisica}</em>
            </li>
          ))}
        </ul>
      </details>

      <details>
        <summary>Qué hicimos con tus datos</summary>
        <ul>
          <li>Transformaciones: {explainability.transformaciones.join("; ")}.</li>
          {explainability.data_cleaning.length === 0 ? (
            <li>No hubo que limpiar ni reemplazar datos.</li>
          ) : (
            explainability.data_cleaning.map((c, i) => (
              <li key={i}>
                {c.accion} en <code>{c.columna}</code> ({c.filas} fila/s): {c.motivo}.
              </li>
            ))
          )}
        </ul>
      </details>
    </div>
  );
}
