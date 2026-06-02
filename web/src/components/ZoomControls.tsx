import type { BoxZoom } from "./useBoxZoom";

/** Pista de "arrastrá para hacer zoom" o botón de reset, según el estado. */
export function ZoomControls({ zoom }: { zoom: BoxZoom }) {
  return zoom.isZoomed ? (
    <button type="button" className="chart__reset" onClick={zoom.reset}>
      ↺ ver todo
    </button>
  ) : (
    <span className="chart__hint">⤢ arrastrá para hacer zoom</span>
  );
}
