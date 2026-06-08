import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const adminTarget = process.env.VITE_ADMIN_API_URL ?? "http://127.0.0.1:8741";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/health": adminTarget,
      "/status": adminTarget,
      "/capabilities": adminTarget,
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
