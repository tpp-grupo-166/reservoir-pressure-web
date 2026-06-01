import { useState } from "react";
import type { PredictResponse } from "./types";
import { Wizard } from "./components/Wizard";
import { TrajectoryChart } from "./components/TrajectoryChart";
import { ExplainPanel } from "./components/ExplainPanel";

export default function App() {
  const [result, setResult] = useState<PredictResponse | null>(null);

  return (
    <div className="app">
      <header className="app__header">
        <h1>Estimador de presión de reservorio</h1>
        <p>Cargá la historia de producción y la tabla PVT para estimar la trayectoria de presión.</p>
      </header>

      {!result ? (
        <Wizard onResult={setResult} />
      ) : (
        <section className="result">
          <TrajectoryChart prediction={result.prediction} baseline={result.baseline} />
          <ExplainPanel explainability={result.explainability} modelInfo={result.model_info} />
          <button className="result__again" onClick={() => setResult(null)}>
            ← Nueva estimación
          </button>
        </section>
      )}
    </div>
  );
}
