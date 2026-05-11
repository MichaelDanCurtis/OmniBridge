import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiTarget = process.env.VITE_OMNIBRIDGE_API_TARGET ?? "http://127.0.0.1:8001";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ["host.docker.internal"],
    proxy: {
      "/analysis": apiTarget,
      "/approvals": apiTarget,
      "/artifacts": apiTarget,
      "/blueprints": apiTarget,
      "/collectors": apiTarget,
      "/estimates": apiTarget,
      "/discovery-runs": apiTarget,
      "/execution-plans": apiTarget,
      "/graph": apiTarget,
      "/health": apiTarget,
      "/imports": apiTarget,
      "/migration-waves": apiTarget,
      "/validation": apiTarget,
      "/workspace": apiTarget,
    },
  },
});
