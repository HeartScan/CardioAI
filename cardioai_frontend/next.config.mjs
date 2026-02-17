/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  images: {
    unoptimized: false,
  },
  reactStrictMode: true,
  compiler: {
    // Keeps styled-components transform if needed, though project uses Tailwind
    styledComponents: true
  },
  experimental: {
    webpackBuildWorker: true,
  },
}

export default nextConfig;
