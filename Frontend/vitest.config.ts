import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

// Minimal unit-test harness. The suite targets pure library logic (no DOM), so
// the default Node environment is enough; File/Blob are Node globals (>=18).
export default defineConfig({
  resolve: {
    // Mirrors the "@/*" path alias from tsconfig.json.
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
