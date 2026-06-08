import { useEffect, useState } from "react";
import type { PredictResponse, StaticProps, ValidateResponse } from "../types";
import { predict, validateInput } from "../api/client";
import { validateStaticProps } from "../utils/validation";
import { EXAMPLE_STATIC, exampleFiles } from "../exampleData";
import { FileDrop } from "./FileDrop";
import { StepIndicator } from "./StepIndicator";
import { CsvPreviewTable } from "./CsvPreviewTable";
import { ValidationFeedback } from "./ValidationFeedback";

const DEFAULT_STATIC: StaticProps = {
  porosidad: 0.24,
  permeabilidad_mD: 400,
  espesor_neto_m: 170,
  area_m2: 16_000_000,
  presion_inicial_psi: 4100,
};

const STATIC_FIELDS: { key: keyof StaticProps; label: string; unit: string }[] = [
  { key: "porosidad", label: "Porosidad", unit: "0–1" },
  { key: "permeabilidad_mD", label: "Permeabilidad", unit: "mD" },
  { key: "espesor_neto_m", label: "Espesor neto", unit: "m" },
  { key: "area_m2", label: "Área", unit: "m²" },
  { key: "presion_inicial_psi", label: "Presión inicial", unit: "psi" },
];

interface Props {
  onResult: (r: PredictResponse) => void;
  onStepChange?: (step: number) => void;
}

/** Wizard de 3 pasos: historia → estáticos → PVT → estimar. */
export function Wizard({ onResult, onStepChange }: Props) {
  const [step, setStep] = useState(0);

  const handleStepChange = (newStep: number) => {
    setStep(newStep);
    onStepChange?.(newStep);
  };
  const [history, setHistory] = useState<File | null>(null);
  const [pvt, setPvt] = useState<File | null>(null);
  const [staticProps, setStaticProps] = useState<StaticProps>(DEFAULT_STATIC);
  const [tomlFile, setTomlFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // True mientras los datos cargados sean los del caso de ejemplo (sin tocar a mano).
  const [exampleLoaded, setExampleLoaded] = useState(false);

  // Validación temprana por paso (el backend es la única fuente de verdad de las
  // reglas de los CSV; el formulario se valida en el cliente por ser un input de UI).
  const [historyVal, setHistoryVal] = useState<ValidateResponse | null>(null);
  const [historyValidating, setHistoryValidating] = useState(false);
  const [pvtVal, setPvtVal] = useState<ValidateResponse | null>(null);
  const [pvtValidating, setPvtValidating] = useState(false);

  const staticErrors = tomlFile ? [] : validateStaticProps(staticProps);
  const staticErrorByField = Object.fromEntries(
    staticErrors.map((e) => [e.field, e.message]),
  );

  // Valida la historia de producción cada vez que cambia el archivo.
  useEffect(() => {
    if (!history) { setHistoryVal(null); return; }
    let cancelled = false;
    setHistoryValidating(true);
    validateInput({ history })
      .then((r) => { if (!cancelled) setHistoryVal(r); })
      .catch((e) => {
        if (!cancelled) {
          setHistoryVal({
            ok: false, n_filas: 0, columnas_detectadas: [], advertencias: [],
            errores: [e instanceof Error ? e.message : String(e)],
          });
        }
      })
      .finally(() => { if (!cancelled) setHistoryValidating(false); });
    return () => { cancelled = true; };
  }, [history]);

  // Valida la PVT cuando cambia el archivo o la presión inicial (habilita el aviso de rango).
  // En modo TOML no conocemos la presión inicial en el front → sólo se chequean columnas.
  useEffect(() => {
    if (!pvt) { setPvtVal(null); return; }
    let cancelled = false;
    setPvtValidating(true);
    const presionInicialPsi = tomlFile ? undefined : staticProps.presion_inicial_psi;
    validateInput({ pvt, presionInicialPsi })
      .then((r) => { if (!cancelled) setPvtVal(r); })
      .catch((e) => {
        if (!cancelled) {
          setPvtVal({
            ok: false, n_filas: 0, columnas_detectadas: [], advertencias: [],
            errores: [e instanceof Error ? e.message : String(e)],
          });
        }
      })
      .finally(() => { if (!cancelled) setPvtValidating(false); });
    return () => { cancelled = true; };
  }, [pvt, tomlFile, staticProps.presion_inicial_psi]);

  const historyBlocked = historyValidating || (historyVal != null && !historyVal.ok);
  const pvtBlocked = pvtValidating || (pvtVal != null && !pvtVal.ok);

  async function run() {
    if (!history || !pvt) return;
    setLoading(true);
    setError(null);
    try {
      // Si se cargó un TOML, tiene prioridad sobre el formulario.
      const props = tomlFile ? { tomlFile } : staticProps;
      onResult(await predict(history, pvt, props));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  /** Carga el caso de ejemplo (Volve) en los tres pasos y salta al último. */
  function loadExample() {
    const { history: h, pvt: p } = exampleFiles();
    setHistory(h);
    setPvt(p);
    setTomlFile(null);
    setStaticProps(EXAMPLE_STATIC);
    setError(null);
    setExampleLoaded(true);
    handleStepChange(2);
  }

  return (
    <div>
      <StepIndicator currentStep={step} />

      {exampleLoaded && (
        <p className="wizard__loaded">Caso de ejemplo cargado</p>
      )}

      <div className="wizard-card">

        {/* ── Paso 0: Historia de producción ── */}
        {step === 0 && (
          <>
            <h1 className="wizard-card__title">Historia de producción</h1>
            <FileDrop
              label="el CSV de producción"
              file={history}
              onSelect={(f) => { setHistory(f); setExampleLoaded(false); }}
            />
            <ValidationFeedback result={historyVal} validating={historyValidating} />
            <CsvPreviewTable file={history} />
            <p className="wizard__example">
              <button className="linkish" onClick={loadExample}>
                Cargar caso de ejemplo
              </button>
            </p>
            <div className="wizard-nav wizard-nav--end">
              <button className="btn-primary" disabled={!history || historyBlocked} onClick={() => handleStepChange(1)}>
                Siguiente
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_forward</span>
              </button>
            </div>
          </>
        )}

        {/* ── Paso 1: Propiedades del reservorio ── */}
        {step === 1 && (
          <>
            <h1 className="wizard-card__title">Propiedades del reservorio</h1>

            <label className="form-field__label" style={{ display: 'block', marginBottom: '8px' }}>
              Importar configuración
            </label>
            <FileDrop
              label="un config TOML"
              accept=".toml"
              file={tomlFile}
              onSelect={(f) => { setTomlFile(f); setExampleLoaded(false); }}
            />

            {tomlFile ? (
              <p className="field__hint">
                Usando <code>{tomlFile.name}</code>.{' '}
                <button className="linkish" onClick={() => setTomlFile(null)}>Cargar manualmente</button>
              </p>
            ) : (
              <>
                <div className="form-divider">
                  <div className="form-divider__line" />
                  <span className="form-divider__label">Ingreso manual</span>
                  <div className="form-divider__line" />
                </div>

                <div className="form-grid">
                  {STATIC_FIELDS.slice(0, 4).map((f) => (
                    <div key={f.key} className="form-field">
                      <label className="form-field__label" htmlFor={f.key}>
                        {f.label} ({f.unit})
                      </label>
                      <input
                        id={f.key}
                        type="number"
                        className={`form-field__input${staticErrorByField[f.key] ? " form-field__input--error" : ""}`}
                        value={staticProps[f.key]}
                        onChange={(e) => {
                          setStaticProps({ ...staticProps, [f.key]: Number(e.target.value) });
                          setExampleLoaded(false);
                        }}
                      />
                      {staticErrorByField[f.key] && (
                        <p className="form-field__error">{staticErrorByField[f.key]}</p>
                      )}
                    </div>
                  ))}
                </div>
                {/* Presión inicial — ancho completo */}
                <div className="form-field" style={{ marginTop: '0' }}>
                  <label className="form-field__label" htmlFor="presion_inicial_psi">
                    {STATIC_FIELDS[4].label} ({STATIC_FIELDS[4].unit})
                  </label>
                  <input
                    id="presion_inicial_psi"
                    type="number"
                    className={`form-field__input${staticErrorByField.presion_inicial_psi ? " form-field__input--error" : ""}`}
                    value={staticProps.presion_inicial_psi}
                    onChange={(e) => {
                      setStaticProps({ ...staticProps, presion_inicial_psi: Number(e.target.value) });
                      setExampleLoaded(false);
                    }}
                  />
                  {staticErrorByField.presion_inicial_psi && (
                    <p className="form-field__error">{staticErrorByField.presion_inicial_psi}</p>
                  )}
                </div>
              </>
            )}

            <div className="wizard-nav">
              <button className="btn-back" onClick={() => handleStepChange(0)}>Atrás</button>
              <button className="btn-primary" disabled={staticErrors.length > 0} onClick={() => handleStepChange(2)}>
                Siguiente
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_forward</span>
              </button>
            </div>
          </>
        )}

        {/* ── Paso 2: Tabla PVT ── */}
        {step === 2 && (
          <>
            <h1 className="wizard-card__title">Tabla PVT</h1>
            <label className="form-field__label" style={{ display: 'block', marginBottom: '8px' }}>
              Cargá la tabla PVT para completar la carga de datos
            </label>
            <FileDrop
              label="el CSV de la tabla PVT"
              file={pvt}
              onSelect={(f) => { setPvt(f); setExampleLoaded(false); }}
            />
            <ValidationFeedback result={pvtVal} validating={pvtValidating} />
            <CsvPreviewTable file={pvt} />
            {error && <p className="error" style={{ marginTop: '16px' }}>⚠ {error}</p>}
            <div className="wizard-nav">
              <button className="btn-back" onClick={() => handleStepChange(1)}>Atrás</button>
              <button className="btn-primary" disabled={!pvt || loading || pvtBlocked} onClick={run}>
                {loading ? 'Estimando…' : 'Estimar presión'}
                {!loading && (
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_forward</span>
                )}
              </button>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
