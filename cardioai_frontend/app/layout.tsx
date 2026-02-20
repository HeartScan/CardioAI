import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import ConditionalFooter from '@/components/ConditionalFooter'
import { Toaster } from 'sonner'

// Initialize Inter font but handle it safely
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'HeartScan - Heart Rate Monitoring using Chest Vibrations',
  description: 'Your phone can detect your heartbeat using tiny chest vibrations. No wearables, no registration, just place your phone on your chest.',
  metadataBase: new URL('https://heartscan.app'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: 'HeartScan - Heart Rate Monitoring using Chest Vibrations',
    description: 'Monitor your heart health accurately using just your smartphone. Space technology, clinically validated.',
    url: 'https://heartscan.app',
    siteName: 'HeartScan',
    images: [
      {
        url: '/images/logo.webp',
        width: 800,
        height: 600,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'HeartScan - Heart Rate Monitoring',
    description: 'Measure your heart rate using your phone. Space technology from Yuri Gagarin mission era, now in your pocket.',
    images: ['/images/logo.webp'],
  },
  verification: {
    google: 'google-site-verification=YOUR_VERIFICATION_CODE',
    other: {
      'app-ads-txt-validator': 'app-ads.txt',
    }
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/cropped-logo-icon-192x192.png',
  },
}

// Export viewport settings separately
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* This ensures app-ads.txt is properly recognized by app stores */}
        <link rel="app-ads-txt" href="/app-ads.txt" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/cropped-logo-icon-192x192.png" />
        
        {/* DNS prefetching for performance */}
        <link rel="dns-prefetch" href="https://heartscan.app" />
      </head>
      <body className={`font-sans min-h-screen ${inter.className}`}>
        <Providers>
          <div className="flex flex-col min-h-screen">
            <main className="flex-grow">{children}</main>
            <ConditionalFooter />
          </div>
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}
