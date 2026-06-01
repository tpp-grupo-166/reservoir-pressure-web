import {
  Area, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { Baseline, Prediction } from "../types";
import { TOOLTIP_PROPS } from "./chartTheme";

interface Props {
  prediction: Prediction;
  baseline: Baseline;
  bubblePoint: number | null;
}

/** Presión estimada vs tiempo, con banda de incertidumbre, baseline y punto de burbuja. */
export function TrajectoryChart({ prediction, baseline, bubblePoint }: Props) {
  const data = prediction.tiempo_dias.map((t, i) => ({
    t,
    estimada: prediction.presion_estimada_psi[i],
    baseline: baseline.presion_psi[i],
    banda: [prediction.banda_inferior_psi[i], prediction.banda_superior_psi[i]] as [number, number],
  }));

  return (
    <div className="chart">
      <div className="chart__header">
        <span className="chart__title">Presión estimada vs tiempo</span>
        <span className="info" tabIndex={0} role="button" aria-label="Qué significan las líneas">
          i
          <span className="info__tip" role="tooltip">
            <span>
              <strong>Estimada</strong> (azul): la presión que predice el modelo para tu campo.
              La <strong>banda</strong> es el rango entre las distintas corridas (incertidumbre).
            </span>
            <span>
              <strong>Curva promedio</strong> (gris punteada): el comportamiento típico del set de
              entrenamiento, como referencia. Si las líneas se separan, el modelo responde a tus
              datos; si van pegadas, no aporta más que el promedio.
            </span>
            <span>
              <strong>Punto de burbuja</strong> (línea naranja): por debajo se libera gas y cambia
              el régimen. Ninguna curva es la presión real medida: es una estimación.
            </span>
          </span>
        </span>
      </div>
      <ResponsiveContainer width="100%" height={380}>
        <ComposedChart data={data} margin={{ top: 8, right: 24, bottom: 36, left: 24 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="t"
            type="number"
            domain={[0, "dataMax"]}
            allowDecimals={false}
            tickFormatter={(v) => `${Math.round(v)}`}
            label={{ value: "tiempo (días)", position: "insideBottom", offset: -10, dy: 12 }}
          />
          <YAxis label={{ value: "presión (psi)", angle: -90, position: "insideLeft", dx: -12 }} domain={["auto", "auto"]} />
          <Tooltip {...TOOLTIP_PROPS} formatter={(v) => (typeof v === "number" ? `${v.toFixed(1)} psi` : String(v))} />
          <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: 12 }} />
          <Area type="monotone" dataKey="banda" name="incertidumbre" stroke="none" fill="#1f77b4" fillOpacity={0.15} />
          <Line type="monotone" dataKey="estimada" name="estimada" stroke="#1f77b4" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="baseline" name={baseline.nombre} stroke="#888" dot={false} strokeDasharray="5 5" />
          {bubblePoint != null && (
            <ReferenceLine y={bubblePoint} stroke="#e8833a" strokeDasharray="4 4"
              label={{ value: `Pb ${bubblePoint.toFixed(0)} psi`, position: "insideTopRight", fill: "#e8833a", fontSize: 11 }} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
