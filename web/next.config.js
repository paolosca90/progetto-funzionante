/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable PWA features
  experimental: {
    appDir: true,
    optimizePackageImports: ['@heroicons/react', 'lucide-react', 'framer-motion'],
  },

  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Bundle optimization
  webpack: (config, { dev, isServer }) => {
    // Bundle analyzer in development
    if (!dev && !isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10,
            reuseExistingChunk: true,
          },
          trading: {
            test: /[\\/]components[\\/]trading[\\/]/,
            name: 'trading',
            priority: 20,
            reuseExistingChunk: true,
          },
          charts: {
            test: /[\\/]components[\\/]charts[\\/]/,
            name: 'charts',
            priority: 20,
            reuseExistingChunk: true,
          },
        },
      };
    }

    // Optimize for mobile bundle size
    config.resolve.alias = {
      ...config.resolve.alias,
      'framer-motion': dev ? 'framer-motion' : 'framer-motion/dist/framer-motion',
    };

    return config;
  },

  // Mobile-first optimization
  images: {
    domains: ['localhost'],
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [320, 420, 768, 1024, 1200],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 86400, // 24 hours
  },

  // API proxy to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/:path*',
      },
    ];
  },

  // Security and performance headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          // Performance headers
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          // Cache static assets aggressively
          ...(process.env.NODE_ENV === 'production' ? [
            {
              key: 'Cache-Control',
              value: 'public, max-age=31536000, immutable',
            },
          ] : []),
        ],
      },
      // Service Worker
      {
        source: '/sw.js',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=0, must-revalidate',
          },
        ],
      },
    ];
  },

  // Output optimization
  output: 'standalone',

  // Compress output
  compress: true,

  // Enable SWC minification for better performance
  swcMinify: true,

  // Reduce build size
  modularizeImports: {
    '@heroicons/react/24/outline': {
      transform: '@heroicons/react/24/outline/{{member}}',
    },
    '@heroicons/react/24/solid': {
      transform: '@heroicons/react/24/solid/{{member}}',
    },
    'lucide-react': {
      transform: 'lucide-react/dist/esm/icons/{{kebabCase member}}',
    },
  },
}

module.exports = nextConfig;