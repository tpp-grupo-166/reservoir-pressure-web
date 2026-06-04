// Caso de ejemplo para recorrer el wizard sin tener datos a mano: simulación 1
// del campo Volve (el mismo `sample-data/` del repo, importado como única fuente
// de verdad vía `?raw` para no duplicar los CSV).
import produccionCsv from "../../sample-data/produccion_ejemplo.csv?raw";
import pvtCsv from "../../sample-data/pvt_ejemplo.csv?raw";
import type { StaticProps } from "./types";

export const EXAMPLE_LABEL = "Volve · simulación 1";

// Espejo de `sample-data/reservorio_ejemplo.toml` (propiedades estáticas del campo).
export const EXAMPLE_STATIC: StaticProps = {
  porosidad: 0.239,
  permeabilidad_mD: 2353.78,
  espesor_neto_m: 77.75,
  area_m2: 6_796_200,
  presion_inicial_psi: 4773.49,
};

function csvFile(content: string, name: string): File {
  return new File([content], name, { type: "text/csv" });
}

/** CSVs del caso de ejemplo como objetos `File`, listos para el wizard. */
export function exampleFiles(): { history: File; pvt: File } {
  return {
    history: csvFile(produccionCsv, "produccion_ejemplo.csv"),
    pvt: csvFile(pvtCsv, "pvt_ejemplo.csv"),
  };
}
