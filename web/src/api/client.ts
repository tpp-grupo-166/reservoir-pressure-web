// Cliente HTTP tipado del backend. Vite proxea /api → :8000.
import type { ModelInfo, PredictResponse, StaticProps, ValidateResponse } from "../types";

async function asError(res: Response): Promise<never> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    detail = body.detail ?? detail;
  } catch {
    /* respuesta sin JSON */
  }
  throw new Error(detail);
}

export async function getModelInfo(): Promise<ModelInfo> {
  const res = await fetch("/api/model-info");
  if (!res.ok) return asError(res);
  return res.json();
}

/**
 * Valida la historia y/o la tabla PVT antes de predecir (feedback por paso del wizard).
 * Se manda sólo el archivo del paso actual; la presión inicial habilita el aviso de
 * rango de la PVT.
 */
export async function validateInput(opts: {
  history?: File;
  pvt?: File;
  presionInicialPsi?: number;
}): Promise<ValidateResponse> {
  const form = new FormData();
  if (opts.history) form.append("history_csv", opts.history);
  if (opts.pvt) form.append("pvt_csv", opts.pvt);
  if (opts.presionInicialPsi != null) {
    form.append("presion_inicial_psi", String(opts.presionInicialPsi));
  }
  const res = await fetch("/api/validate", { method: "POST", body: form });
  if (!res.ok) return asError(res);
  return res.json();
}

export async function predict(
  historyCsv: File,
  pvtCsv: File,
  // Propiedades del reservorio: o un archivo TOML, o el objeto del formulario.
  staticProps: StaticProps | { tomlFile: File },
): Promise<PredictResponse> {
  const form = new FormData();
  form.append("history_csv", historyCsv);
  form.append("pvt_csv", pvtCsv);
  if ("tomlFile" in staticProps) {
    form.append("static_toml", staticProps.tomlFile);
  } else {
    form.append("static_props", JSON.stringify(staticProps));
  }
  const res = await fetch("/api/predict", { method: "POST", body: form });
  if (!res.ok) return asError(res);
  return res.json();
}
