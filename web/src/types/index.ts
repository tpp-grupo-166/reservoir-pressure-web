// Espejo del contrato de la API (api/schemas.py). Mantener en sync.

export interface StaticProps {
  porosidad: number;
  permeabilidad_mD: number;
  espesor_neto_m: number;
  area_m2: number;
  presion_inicial_psi: number;
}

export interface Prediction {
  tiempo_dias: number[];
  presion_estimada_psi: number[];
  presion_inicial_psi: number;
}

export interface Baseline {
  nombre: string;
  presion_psi: number[];
}

export interface FeatureDoc {
  nombre: string;
  descripcion: string;
  fisica: string;
}

export interface CleaningStep {
  accion: string;
  columna: string;
  filas: number;
  motivo: string;
}

export interface Explainability {
  features_construidos: FeatureDoc[];
  data_cleaning: CleaningStep[];
  transformaciones: string[];
  advertencias: string[];
}

export interface ValidationMetrics {
  R2_medio: number;
  R2_std: number;
  MAE_psi: number;
}

export interface ModelInfo {
  version: string;
  metricas_validacion: ValidationMetrics;
  nota: string;
}

export interface PredictResponse {
  prediction: Prediction;
  baseline: Baseline;
  explainability: Explainability;
  model_info: ModelInfo;
}

export interface ValidateResponse {
  ok: boolean;
  n_filas: number;
  columnas_detectadas: string[];
  advertencias: string[];
  errores: string[];
}
