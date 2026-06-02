import { useCallback, useState } from "react";

/**
 * Zoom por recuadro para gráficos de recharts: el usuario arrastra de
 * izquierda a derecha sobre el área del chart y al soltar se acota el
 * dominio del eje X a esa ventana. Doble click o el botón "reset" vuelve
 * a la vista completa. Recharts no trae esto nativo; se arma con los
 * handlers del chart + un <ReferenceArea> que dibuja la selección.
 */

// recharts pasa el estado del chart en cada handler; solo nos importa activeLabel.
interface ChartState {
  activeLabel?: string | number;
}

export interface BoxZoom {
  /** [min, max] para <XAxis domain={...} />. */
  domain: [number | string, number | string];
  /** Bordes de la selección en curso (null cuando no se está arrastrando). */
  refLeft: number | null;
  refRight: number | null;
  /** true si hay un recorte activo (muestra el botón de reset). */
  isZoomed: boolean;
  onMouseDown: (e: ChartState | null) => void;
  onMouseMove: (e: ChartState | null) => void;
  onMouseUp: () => void;
  reset: () => void;
}

const FULL: [number, number | string] = [0, "dataMax"];

export function useBoxZoom(): BoxZoom {
  const [refLeft, setRefLeft] = useState<number | null>(null);
  const [refRight, setRefRight] = useState<number | null>(null);
  const [domain, setDomain] = useState<[number | string, number | string]>(FULL);

  const onMouseDown = useCallback((e: ChartState | null) => {
    if (e?.activeLabel != null) {
      setRefLeft(Number(e.activeLabel));
      setRefRight(null);
    }
  }, []);

  const onMouseMove = useCallback(
    (e: ChartState | null) => {
      if (refLeft !== null && e?.activeLabel != null) setRefRight(Number(e.activeLabel));
    },
    [refLeft],
  );

  const onMouseUp = useCallback(() => {
    if (refLeft !== null && refRight !== null && refLeft !== refRight) {
      const lo = Math.min(refLeft, refRight);
      const hi = Math.max(refLeft, refRight);
      setDomain([lo, hi]);
    }
    setRefLeft(null);
    setRefRight(null);
  }, [refLeft, refRight]);

  const reset = useCallback(() => setDomain(FULL), []);

  return {
    domain,
    refLeft,
    refRight,
    isZoomed: domain[0] !== FULL[0] || domain[1] !== FULL[1],
    onMouseDown,
    onMouseMove,
    onMouseUp,
    reset,
  };
}
