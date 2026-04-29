import type { NextConfig } from "next";
import { createRequire } from "node:module";

/**
 * FR-F15: Restrict remote image hosts (explicit allowlist, no wildcards).
 * FR-F20: Optional bundle analyzer gated by ANALYZE=1 (fails open if missing).
 */
const baseConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "logo.clearbit.com" },
      { protocol: "https", hostname: "assets.stockmanager.dev" },
      { protocol: "https", hostname: "raw.githubusercontent.com" },
    ],
  },
};

type ConfigTransform = (cfg: NextConfig) => NextConfig;

function maybeAnalyzer(): ConfigTransform {
  if (process.env.ANALYZE !== "1") return (cfg) => cfg;
  try {
    const require = createRequire(import.meta.url);
    const withAnalyzer = require("@next/bundle-analyzer") as (
      opts: { enabled: boolean },
    ) => ConfigTransform;
    return withAnalyzer({ enabled: true });
  } catch {
    // eslint-disable-next-line no-console
    console.warn(
      "[next.config] ANALYZE=1 but @next/bundle-analyzer is not installed; proceeding without analyzer.",
    );
    return (cfg) => cfg;
  }
}

const nextConfig: NextConfig = maybeAnalyzer()(baseConfig);

export default nextConfig;
