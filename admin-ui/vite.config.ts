/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const adminTarget = process.env.VITE_ADMIN_API_URL ?? "http://127.0.0.1:8741";
const vitePort = Number(process.env.MYCELIUM_ADMIN_UI_PORT ?? "5173");

export default defineConfig({
  plugins: [react()],
  server: {
    port: Number.isFinite(vitePort) ? vitePort : 5173,
    proxy: {
      "/health": adminTarget,
      "/status": adminTarget,
      "/capabilities": adminTarget,
      "/query": adminTarget,
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  test: {
    environment: "node",
  },
});
