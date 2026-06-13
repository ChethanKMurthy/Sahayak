/** @type {import('next').NextConfig} */
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  // Standalone server output for a small production Docker image.
  output: "standalone",
  // Allow importing the shared i18n/DSL JSON from the monorepo /shared dir.
  experimental: { externalDir: true },
  // Proxy /api/* to the FastAPI backend in dev so the browser hits one origin.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;
