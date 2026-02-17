import { defineConfig } from "vitest/config";

/**
 * Vitest configuration for StacksOrbit.
 * This configuration uses the @stacks/clarinet-sdk/vitest environment
 * to provide native simnet support for Clarity smart contracts.
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
      // Ensure tests are isolated and don't conflict
      pool: 'threads',
    },
  };
});
