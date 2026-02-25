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
  async redirects() {
    return [
      {
        source: '/cardio-ai',
        destination: '/',
        permanent: true,
      },
      {
        source: '/cardio-ai/:path*',
        destination: '/',
        permanent: true,
      },
    ]
  },
}

export default nextConfig;
