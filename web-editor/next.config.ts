import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  redirects: async () => [{ source: "/docs", destination: "/docs/index.html", permanent: false }],
  experimental: {
    reactCompiler: true,
  },
};

export default nextConfig;
