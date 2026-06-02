import {
  CartesianGrid, Legend, Line, LineChart, ReferenceArea,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { Drivers } from "../types";
import { TOOLTIP_PROPS } from "./chartTheme";
import { useBoxZoom } from "./useBoxZoom";
import { ZoomControls } from "./ZoomControls";

interface Props {
  tiempoDias: number[];
  drivers: Drivers;
}

/** Caudales de producción e inyección: el contexto de entrada que mueve la presión. */
export function DriversChart({ tiempoDias, drivers }: Props) {
  const zoom = useBoxZoom();
  const data = tiempoDias.map((t, i) => ({
    t,
    petroleo: drivers.caudal_petroleo_bbl[i],
    inyeccion: drivers.caudal_iny_agua_bbl[i],
  }));

  return (
    <div className="chart">
      <div className="chart__header">
        <span className="chart__title">Caudales de producción e inyección</span>
        <span className="info" tabIndex={0} role="button" aria-label="Qué muestran los caudales">
          i
          <span className="info__tip" role="tooltip">
            <span>Los datos de entrada que mueven la presión: cuánto petróleo se extrae y cuánta agua se inyecta.</span>
            <span>Ayudan a leer la trayectoria de presión en su contexto de operación.</span>
          </span>
        </span>
        <ZoomControls zoom={zoom} />
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart
          data={data}
          margin={{ top: 8, right: 24, bottom: 36, left: 24 }}
          onMouseDown={zoom.onMouseDown}
          onMouseMove={zoom.onMouseMove}
          onMouseUp={zoom.onMouseUp}
          onDoubleClick={zoom.reset}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="t"
            type="number"
            domain={zoom.domain}
            allowDataOverflow
            allowDecimals={false}
            tickFormatter={(v) => `${Math.round(v)}`}
            label={{ value: "tiempo (días)", position: "insideBottom", offset: -10, dy: 12 }}
          />
          <YAxis
            width={72}
            label={{ value: "caudal (bbl/día)", angle: -90, position: "insideLeft", textAnchor: "middle", dx: -4 }}
            domain={["auto", "auto"]}
          />
          <Tooltip {...TOOLTIP_PROPS} formatter={(v) => (typeof v === "number" ? `${v.toFixed(0)} bbl/día` : String(v))} />
          <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: 12 }} />
          <Line type="monotone" dataKey="petroleo" name="petróleo producido" stroke="#1f77b4" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="inyeccion" name="agua inyectada" stroke="#17a2b8" dot={false} strokeWidth={2} />
          {zoom.refLeft !== null && zoom.refRight !== null && (
            <ReferenceArea x1={zoom.refLeft} x2={zoom.refRight} fill="#17a2b8" fillOpacity={0.2} />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
