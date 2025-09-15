import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/providers/auth-provider'
import { ThemeProvider } from '@/providers/theme-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Cash Revolution - Trading Platform',
  description: 'Mobile-first AI-powered trading signal platform with real-time execution',
  keywords: ['trading', 'AI', 'signals', 'forex', 'mobile', 'real-time'],
  authors: [{ name: 'AI Cash Revolution Team' }],
  creator: 'AI Cash Revolution',
  publisher: 'AI Cash Revolution',

  // Mobile optimization
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },

  // PWA Manifest
  manifest: '/manifest.json',

  // Apple Touch Icon
  icons: {
    apple: '/icons/apple-touch-icon.png',
    icon: [
      { url: '/icons/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/icons/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
  },

  // Open Graph for social sharing
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://aicash-revolution.com',
    siteName: 'AI Cash Revolution',
    title: 'AI Cash Revolution - Trading Platform',
    description: 'Mobile-first AI-powered trading signal platform',
    images: [
      {
        url: '/images/og-image.png',
        width: 1200,
        height: 630,
        alt: 'AI Cash Revolution Trading Platform',
      },
    ],
  },

  // Twitter Card
  twitter: {
    card: 'summary_large_image',
    title: 'AI Cash Revolution',
    description: 'Mobile-first AI trading platform',
    images: ['/images/twitter-image.png'],
  },

  // Mobile app capabilities
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'AI Cash Revolution',
  },

  // Theme color for mobile browsers
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#0ea5e9' },
    { media: '(prefers-color-scheme: dark)', color: '#0f172a' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Preconnect to external domains for performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />

        {/* Mobile-specific meta tags */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="format-detection" content="telephone=no" />

        {/* Disable zoom on mobile */}
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
      </head>
      <body className={`${inter.className} bg-white dark:bg-dark-900 text-dark-900 dark:text-white min-h-screen`}>
        <ThemeProvider>
          <AuthProvider>
            {/* Mobile-first layout */}
            <div className="flex flex-col min-h-screen">
              {/* Main content area */}
              <main className="flex-1 relative">
                {children}
              </main>
            </div>

            {/* Toast notifications - mobile optimized */}
            <Toaster
              position="top-center"
              toastOptions={{
                duration: 3000,
                style: {
                  background: '#1e293b',
                  color: '#fff',
                  fontSize: '14px',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  maxWidth: '90vw',
                },
                success: {
                  iconTheme: {
                    primary: '#22c55e',
                    secondary: '#fff',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}