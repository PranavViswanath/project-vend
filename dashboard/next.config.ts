import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel best practice: bundle-dynamic-imports
  // Optimize Framer Motion bundle size
  experimental: {
    optimizePackageImports: ['framer-motion'],
  },
};

export default nextConfig;
