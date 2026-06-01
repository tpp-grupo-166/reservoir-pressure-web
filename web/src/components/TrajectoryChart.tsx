import {
  CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { Baseline, Prediction } from "../types";

interface Props {
  prediction: Prediction;
  baseline: Baseline;
}

/** Presión estimada vs tiempo, con baseline superpuesto. */
export function TrajectoryChart({ prediction, baseline }: Props) {
  const data = prediction.tiempo_dias.map((t, i) => ({
    t,
    estimada: prediction.presion_estimada_psi[i],
    baseline: baseline.presion_psi[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis dataKey="t" label={{ value: "tiempo (días)", position: "insideBottom", offset: -4 }} />
        <YAxis label={{ value: "presión (psi)", angle: -90, position: "insideLeft" }} domain={["auto", "auto"]} />
        <Tooltip formatter={(v) => (typeof v === "number" ? `${v.toFixed(1)} psi` : String(v))} />
        <Legend />
        <Line type="monotone" dataKey="estimada" name="estimada" stroke="#1f77b4" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="baseline" name={baseline.nombre} stroke="#888" dot={false} strokeDasharray="5 5" />
      </LineChart>
    </ResponsiveContainer>
  );
}
