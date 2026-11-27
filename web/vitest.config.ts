import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: [
      "src/**/*.test.ts",
      "src/**/*.test.tsx",
    ],
    exclude: [
      "e2e/**",
      "node_modules/**",
      ".next/**",
      "playwright-report/**",
      "test-results/**",
    ],
    passWithNoTests: false,
    coverage: {
      include: [
        "src/**/*.ts",
        "src/**/*.tsx",
      ],
      exclude: [
        "src/**/*.d.ts",
        "src/app/**",
      ],
    },
  },
});
