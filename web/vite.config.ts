import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy de /api al backend FastAPI en desarrollo.
    proxy: {
      "/api": "http://localhost:8000",
    },
    // Permite importar los CSV de `sample-data/` (fuera de `web/`) vía `?raw`.
    fs: { allow: [".."] },
  },
});
