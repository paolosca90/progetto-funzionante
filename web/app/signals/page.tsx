import { Metadata } from 'next'
import dynamic from 'next/dynamic'
import { Suspense } from 'react'
import LoadingSpinner from '@/components/ui/loading-spinner'

// Lazy load signals components
const SignalsLayout = dynamic(() => import('@/components/signals/signals-layout'), {
  loading: () => <LoadingSpinner />,
})

const SignalFilters = dynamic(() => import('@/components/signals/signal-filters'), {
  loading: () => <div className="h-16 skeleton-mobile" />,
})

const SignalsList = dynamic(() => import('@/components/signals/signals-list'), {
  loading: () => <div className="space-y-4">{Array.from({length: 3}).map((_, i) => <div key={i} className="h-32 skeleton-mobile" />)}</div>,
})

export const metadata: Metadata = {
  title: 'Trading Signals - AI Cash Revolution',
  description: 'Real-time AI-powered trading signals for Forex, Commodities, and Indices',
}

export default function SignalsPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <SignalsLayout>
        <div className="space-y-4">
          {/* Signal Filters */}
          <Suspense fallback={<div className="h-16 skeleton-mobile" />}>
            <SignalFilters />
          </Suspense>

          {/* Signals List with Virtual Scrolling */}
          <Suspense fallback={
            <div className="space-y-4">
              {Array.from({length: 3}).map((_, i) => (
                <div key={i} className="h-32 skeleton-mobile" />
              ))}
            </div>
          }>
            <SignalsList />
          </Suspense>
        </div>
      </SignalsLayout>
    </Suspense>
  )
}