import type { ValidateResponse } from "../types";

interface Props {
  result: ValidateResponse | null;
  validating: boolean;
}

/**
 * Feedback de validación de un archivo del wizard: estado "validando", errores
 * que bloquean el paso (rojo), advertencias no bloqueantes (ámbar) o el OK (verde).
 */
export function ValidationFeedback({ result, validating }: Props) {
  if (validating) {
    return <p className="validation validation--checking">Validando datos…</p>;
  }
  if (!result) return null;

  const clean = result.ok && result.advertencias.length === 0;

  return (
    <div className="validation">
      {result.errores.map((e, i) => (
        <p key={`e${i}`} className="validation__error">⚠ {e}</p>
      ))}
      {result.advertencias.map((w, i) => (
        <p key={`w${i}`} className="validation__warning">⚠ {w}</p>
      ))}
      {clean && (
        <p className="validation__ok">
          ✓ Datos válidos{result.n_filas ? ` · ${result.n_filas} filas` : ""}
        </p>
      )}
    </div>
  );
}
