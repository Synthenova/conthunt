/** @type {import('next').NextConfig} */
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const posthogIngestUrl = "https://us.i.posthog.com";
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/ingest/:path*",
        destination: `${posthogIngestUrl}/:path*`,
      },
      {
        source: "/ingest",
        destination: posthogIngestUrl,
      },
      {
        source: "/v1/:path*",
        destination: `${backendUrl}/v1/:path*`,
      },
      {
        source: "/v1",
        destination: `${backendUrl}/v1`,
      },
      {
        source: "/api/:path*",
        destination: `${backendUrl}/v1/:path*`,
      },
      // Handling for root /api calls if any (optional)
      {
        source: "/api",
        destination: `${backendUrl}/v1`,
      }
    ];
  },
};

export default nextConfig;
