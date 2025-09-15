import { Metadata } from 'next'
import dynamic from 'next/dynamic'
import { Suspense } from 'react'
import LoadingSpinner from '@/components/ui/loading-spinner'

// Lazy load dashboard components
const DashboardLayout = dynamic(() => import('@/components/dashboard/dashboard-layout'), {
  loading: () => <LoadingSpinner />,
})

const TradingOverview = dynamic(() => import('@/components/trading/trading-overview'), {
  loading: () => <div className="h-32 skeleton-mobile" />,
})

const PortfolioSummary = dynamic(() => import('@/components/trading/portfolio-summary'), {
  loading: () => <div className="h-48 skeleton-mobile" />,
})

const RecentSignals = dynamic(() => import('@/components/trading/recent-signals'), {
  loading: () => <div className="h-64 skeleton-mobile" />,
})

export const metadata: Metadata = {
  title: 'Dashboard - AI Cash Revolution',
  description: 'Your trading dashboard with real-time signals and portfolio overview',
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <DashboardLayout>
        <div className="space-y-6">
          {/* Trading Overview */}
          <Suspense fallback={<div className="h-32 skeleton-mobile" />}>
            <TradingOverview />
          </Suspense>

          {/* Portfolio Summary */}
          <Suspense fallback={<div className="h-48 skeleton-mobile" />}>
            <PortfolioSummary />
          </Suspense>

          {/* Recent Signals */}
          <Suspense fallback={<div className="h-64 skeleton-mobile" />}>
            <RecentSignals />
          </Suspense>
        </div>
      </DashboardLayout>
    </Suspense>
  )
}