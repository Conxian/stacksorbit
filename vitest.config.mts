import { defineConfig } from "vitest/config";
import { vitestSetupFilePath } from "@stacks/clarinet-sdk/vitest";

/**
 * Vitest configuration for StacksOrbit.
 * Note: .mts extension is mandatory for ESM compatibility with @stacks/clarinet-sdk.
 */
export default defineConfig({
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
});
