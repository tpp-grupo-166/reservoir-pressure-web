import { useState } from 'react';
import type { PredictResponse } from '../types';
import { Wizard } from '../components/Wizard';
import { TrajectoryChart } from '../components/TrajectoryChart';
import { VrrChart } from '../components/VrrChart';
import { DriversChart } from '../components/DriversChart';
import { ExplainPanel } from '../components/ExplainPanel';
import { TopAppBar } from '../components/TopAppBar';
import { NavigationDrawer } from '../components/NavigationDrawer';

export function Dashboard() {
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [step, setStep] = useState(0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: '#f5fafb' }}>
      <TopAppBar />
      <div style={{ display: 'flex', flex: 1 }}>
        <NavigationDrawer activeStep={result ? undefined : step} />
        <main
          className="main-with-drawer"
          style={{ padding: '32px 40px', flex: 1 }}
        >
          {!result ? (
            <Wizard onResult={setResult} onStepChange={setStep} />
          ) : (
            <section className="result">
              <TrajectoryChart
                prediction={result.prediction}
                baseline={result.baseline}
                bubblePoint={result.bubble_point_psi}
              />
              <VrrChart tiempoDias={result.prediction.tiempo_dias} vrr={result.vrr} />
              <DriversChart tiempoDias={result.prediction.tiempo_dias} drivers={result.drivers} />
              <ExplainPanel explainability={result.explainability} modelInfo={result.model_info} />
              <button className="btn-primary" onClick={() => { setResult(null); setStep(0); }}>
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_back</span>
                Nueva estimación
              </button>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
