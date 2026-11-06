import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone is only needed for Docker; Vercel natively handles deployment packaging
  output: process.env.VERCEL ? undefined : 'standalone',
  /* config options here */
};

export default nextConfig;
