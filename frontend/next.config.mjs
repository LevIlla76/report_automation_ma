/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    images: { unoptimized: true },
    // Allow the API base URL to be overridden at build time.
    // In Electron packaged mode: API calls go to FastAPI on port 8000.
    env: {
        NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
    },
};

export default nextConfig;
