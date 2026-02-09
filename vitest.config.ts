import { defineConfig } from "vitest/config";

/**
 * Vitest configuration for StacksOrbit.
 * Using dynamic import for @stacks/clarinet-sdk/vitest to ensure compatibility
 * with both CJS and ESM environments while maintaining .ts extension.
 */
export default defineConfig(async () => {
  const { vitestSetupFilePath } = await import("@stacks/clarinet-sdk/vitest");

  return {
    test: {
      environment: "clarinet",
      globals: true,
      setupFiles: [vitestSetupFilePath],
      environmentOptions: {
        clarinet: {
          manifestPath: "./Clarinet.toml",
        },
      },
    },
  };
});
