import { useState } from "react";
import type { PredictResponse, StaticProps } from "../types";
import { predict } from "../api/client";
import { EXAMPLE_STATIC, exampleFiles } from "../exampleData";
import { FileDrop } from "./FileDrop";
import { StepIndicator } from "./StepIndicator";
import { CsvPreviewTable } from "./CsvPreviewTable";

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
            <CsvPreviewTable file={history} />
            <p className="wizard__example">
              <button className="linkish" onClick={loadExample}>
                Cargar caso de ejemplo
              </button>
            </p>
            <div className="wizard-nav wizard-nav--end">
              <button className="btn-primary" disabled={!history} onClick={() => handleStepChange(1)}>
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
                        className="form-field__input"
                        value={staticProps[f.key]}
                        onChange={(e) => {
                          setStaticProps({ ...staticProps, [f.key]: Number(e.target.value) });
                          setExampleLoaded(false);
                        }}
                      />
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
                    className="form-field__input"
                    value={staticProps.presion_inicial_psi}
                    onChange={(e) => {
                      setStaticProps({ ...staticProps, presion_inicial_psi: Number(e.target.value) });
                      setExampleLoaded(false);
                    }}
                  />
                </div>
              </>
            )}

            <div className="wizard-nav">
              <button className="btn-back" onClick={() => handleStepChange(0)}>Atrás</button>
              <button className="btn-primary" onClick={() => handleStepChange(2)}>
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
            <CsvPreviewTable file={pvt} />
            {error && <p className="error" style={{ marginTop: '16px' }}>⚠ {error}</p>}
            <div className="wizard-nav">
              <button className="btn-back" onClick={() => handleStepChange(1)}>Atrás</button>
              <button className="btn-primary" disabled={!pvt || loading} onClick={run}>
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
