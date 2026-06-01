import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { TOOLTIP_PROPS } from "./chartTheme";

interface Props {
  tiempoDias: number[];
  vrr: number[];
}

/** Voidage Replacement Ratio en el tiempo: explica POR QUÉ sube o baja la presión. */
export function VrrChart({ tiempoDias, vrr }: Props) {
  const data = tiempoDias.map((t, i) => ({ t, vrr: vrr[i] }));

  return (
    <div className="chart">
      <div className="chart__header">
        <span className="chart__title">Voidage Replacement Ratio (VRR)</span>
        <span className="info" tabIndex={0} role="button" aria-label="Qué es el VRR">
          i
          <span className="info__tip" role="tooltip">
            <span>Inyección sobre líquido producido. Es el driver de la presión.</span>
            <span><strong>VRR &gt; 1</strong>: se repone más de lo que se saca → la presión sube.</span>
            <span><strong>VRR &lt; 1</strong>: se saca más de lo que se repone → la presión cae.</span>
          </span>
        </span>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 8, right: 24, bottom: 36, left: 24 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="t"
            type="number"
            domain={[0, "dataMax"]}
            allowDecimals={false}
            tickFormatter={(v) => `${Math.round(v)}`}
            label={{ value: "tiempo (días)", position: "insideBottom", offset: -10, dy: 12 }}
          />
          <YAxis label={{ value: "VRR", angle: -90, position: "insideLeft", dx: -12 }} domain={[0, "auto"]} />
          <Tooltip {...TOOLTIP_PROPS} formatter={(v) => (typeof v === "number" ? v.toFixed(2) : String(v))} />
          <ReferenceLine y={1} stroke="#888" strokeDasharray="4 4"
            label={{ value: "equilibrio (1.0)", position: "insideTopRight", fill: "#888", fontSize: 11 }} />
          <Line type="monotone" dataKey="vrr" name="VRR" stroke="#2ca02c" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
