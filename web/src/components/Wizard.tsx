import { useState } from "react";
import type { PredictResponse, StaticProps } from "../types";
import { predict } from "../api/client";
import { EXAMPLE_STATIC, exampleFiles } from "../exampleData";
import { FileDrop } from "./FileDrop";

const DEFAULT_STATIC: StaticProps = {
  porosidad: 0.24,
  permeabilidad_mD: 400,
  espesor_neto_m: 170,
  area_m2: 16_000_000,
  presion_inicial_psi: 4100,
};

const STATIC_FIELDS: { key: keyof StaticProps; label: string; unit: string }[] = [
  { key: "porosidad", label: "Porosidad", unit: "(0–1)" },
  { key: "permeabilidad_mD", label: "Permeabilidad", unit: "mD" },
  { key: "espesor_neto_m", label: "Espesor neto", unit: "m" },
  { key: "area_m2", label: "Área", unit: "m²" },
  { key: "presion_inicial_psi", label: "Presión inicial", unit: "psi" },
];

interface Props {
  onResult: (r: PredictResponse) => void;
}

/** Wizard de 3 pasos: historia → estáticos → PVT → estimar. */
export function Wizard({ onResult }: Props) {
  const [step, setStep] = useState(0);
  const [history, setHistory] = useState<File | null>(null);
  const [pvt, setPvt] = useState<File | null>(null);
  const [staticProps, setStaticProps] = useState<StaticProps>(DEFAULT_STATIC);
  const [tomlFile, setTomlFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    setStep(2);
  }

  return (
    <div className="wizard">
      <ol className="wizard__steps">
        <li className={step === 0 ? "active" : ""}>1. Producción</li>
        <li className={step === 1 ? "active" : ""}>2. Reservorio</li>
        <li className={step === 2 ? "active" : ""}>3. PVT</li>
      </ol>

      {step === 0 && (
        <section>
          <h3>Historia de producción (CSV)</h3>
          <FileDrop label="el CSV de producción" file={history} onSelect={setHistory} />
          <p className="wizard__example">
            <button className="linkish" onClick={loadExample}>
              Cargar caso de ejemplo
            </button>
          </p>
          <div className="wizard__nav">
            <button disabled={!history} onClick={() => setStep(1)}>Siguiente →</button>
          </div>
        </section>
      )}

      {step === 1 && (
        <section>
          <h3>Propiedades del reservorio</h3>
          <FileDrop label="un config TOML (opcional)" accept=".toml" file={tomlFile} onSelect={setTomlFile} />
          {tomlFile ? (
            <p className="field__hint">
              Usando <code>{tomlFile.name}</code>. <button className="linkish" onClick={() => setTomlFile(null)}>Cargar manualmente</button>
            </p>
          ) : (
            STATIC_FIELDS.map((f) => (
              <label key={f.key} className="field">
                <span>{f.label} <em>{f.unit}</em></span>
                <input
                  type="number"
                  value={staticProps[f.key]}
                  onChange={(e) =>
                    setStaticProps({ ...staticProps, [f.key]: Number(e.target.value) })
                  }
                />
              </label>
            ))
          )}
          <div className="wizard__nav">
            <button onClick={() => setStep(0)}>← Atrás</button>
            <button onClick={() => setStep(2)}>Siguiente →</button>
          </div>
        </section>
      )}

      {step === 2 && (
        <section>
          <h3>Tabla PVT (CSV)</h3>
          <FileDrop label="el CSV de la tabla PVT" file={pvt} onSelect={setPvt} />
          {error && <p className="error">⚠ {error}</p>}
          <div className="wizard__nav">
            <button onClick={() => setStep(1)}>← Atrás</button>
            <button disabled={!pvt || loading} onClick={run}>
              {loading ? "Estimando…" : "Estimar presión"}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
