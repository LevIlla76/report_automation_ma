/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    images: { unoptimized: true },
    // Allow the API base URL to be overridden at build time.
    // When running in Electron (packaged), the frontend is served
    // directly by the FastAPI backend on port 8000, so API calls
    // to /api/... are same-origin. In Next.js dev mode they hit
    // localhost:8000 explicitly.
    env: {
        NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
    },
};

export default nextConfig;
