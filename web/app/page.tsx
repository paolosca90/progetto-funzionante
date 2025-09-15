'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  ChartBarIcon,
  DevicePhoneMobileIcon,
  CpuChipIcon,
  BoltIcon,
  ShieldCheckIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { SignalCard } from '@/components/trading/signal-card'
import { PriceChart } from '@/components/trading/price-chart'
import { StatsOverview } from '@/components/trading/stats-overview'

export default function HomePage() {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-dark-900 dark:via-dark-800 dark:to-dark-900">
      {/* Mobile-First Header */}
      <header className="header-mobile bg-white/90 dark:bg-dark-800/90 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
            <CpuChipIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-dark-900 dark:text-white">AI Cash Revolution</h1>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              {currentTime.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                timeZoneName: 'short'
              })}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/auth/login"
            className="btn-secondary-mobile text-sm px-3 py-2"
          >
            Login
          </Link>
          <Link
            href="/auth/register"
            className="btn-primary-mobile text-sm px-3 py-2"
          >
            Start Free
          </Link>
        </div>
      </header>

      {/* Hero Section - Mobile Optimized */}
      <section className="pt-[80px] pb-8 px-4">
        <div className="max-w-lg mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-6"
          >
            <div className="inline-flex items-center gap-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 px-3 py-1 rounded-full text-sm font-medium">
              <BoltIcon className="w-4 h-4" />
              AI-Powered Trading Signals
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold text-dark-900 dark:text-white leading-tight">
              Trade Smarter with
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-700">
                {' '}AI Signals
              </span>
            </h1>

            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-md mx-auto">
              Get real-time trading signals powered by advanced AI analysis.
              Execute trades directly on MetaTrader 5 with our mobile-first platform.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <Link
                href="/dashboard"
                className="btn-primary-mobile flex-1 flex items-center justify-center gap-2"
              >
                <ChartBarIcon className="w-5 h-5" />
                Start Trading
              </Link>
              <Link
                href="/signals"
                className="btn-secondary-mobile flex-1 flex items-center justify-center gap-2"
              >
                <DevicePhoneMobileIcon className="w-5 h-5" />
                View Signals
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Live Stats - Mobile Cards */}
      <section className="px-4 pb-8">
        <div className="max-w-lg mx-auto">
          <StatsOverview />
        </div>
      </section>

      {/* Featured Signals - Mobile Carousel */}
      <section className="px-4 pb-8">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-dark-900 dark:text-white">
              Latest Signals
            </h2>
            <Link
              href="/signals"
              className="text-primary-600 dark:text-primary-400 text-sm font-medium hover:underline"
            >
              View All
            </Link>
          </div>

          <div className="space-y-4">
            {/* Sample signals - these would come from API */}
            <SignalCard
              signal={{
                id: '1',
                symbol: 'EUR/USD',
                direction: 'BUY',
                entryPrice: 1.0845,
                stopLoss: 1.0820,
                takeProfit: 1.0895,
                confidence: 87,
                timeframe: '1H',
                status: 'active',
                createdAt: new Date(Date.now() - 15 * 60 * 1000).toISOString()
              }}
            />

            <SignalCard
              signal={{
                id: '2',
                symbol: 'GBP/USD',
                direction: 'SELL',
                entryPrice: 1.2456,
                stopLoss: 1.2480,
                takeProfit: 1.2420,
                confidence: 92,
                timeframe: '4H',
                status: 'active',
                createdAt: new Date(Date.now() - 8 * 60 * 1000).toISOString()
              }}
            />
          </div>
        </div>
      </section>

      {/* Quick Chart - Mobile Optimized */}
      <section className="px-4 pb-8">
        <div className="max-w-lg mx-auto">
          <div className="card-mobile">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-dark-900 dark:text-white">
                EUR/USD
              </h3>
              <div className="text-right">
                <div className="text-lg font-bold text-success-600">1.0845</div>
                <div className="text-sm text-success-600">+0.0012 (+0.11%)</div>
              </div>
            </div>
            <PriceChart symbol="EURUSD" height={200} />
          </div>
        </div>
      </section>

      {/* Features Grid - Mobile Optimized */}
      <section className="px-4 pb-12">
        <div className="max-w-lg mx-auto">
          <h2 className="text-2xl font-bold text-center text-dark-900 dark:text-white mb-8">
            Why Choose AI Cash Revolution?
          </h2>

          <div className="grid grid-cols-1 gap-4">
            <FeatureCard
              icon={<CpuChipIcon className="w-6 h-6" />}
              title="AI-Powered Analysis"
              description="Advanced machine learning algorithms analyze multiple market factors in real-time"
            />

            <FeatureCard
              icon={<DevicePhoneMobileIcon className="w-6 h-6" />}
              title="Mobile-First Design"
              description="Optimized for mobile trading with intuitive touch-friendly interface"
            />

            <FeatureCard
              icon={<BoltIcon className="w-6 h-6" />}
              title="Real-Time Execution"
              description="Direct integration with MetaTrader 5 for instant signal execution"
            />

            <FeatureCard
              icon={<ShieldCheckIcon className="w-6 h-6" />}
              title="Risk Management"
              description="Built-in risk controls and position sizing for safer trading"
            />

            <FeatureCard
              icon={<GlobeAltIcon className="w-6 h-6" />}
              title="Global Markets"
              description="Access to Forex, Commodities, and Indices from anywhere"
            />
          </div>
        </div>
      </section>

      {/* CTA Section - Mobile Optimized */}
      <section className="px-4 pb-20">
        <div className="max-w-lg mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-6 text-center text-white"
          >
            <h3 className="text-xl font-bold mb-2">
              Ready to Start Trading?
            </h3>
            <p className="text-primary-100 mb-6">
              Join thousands of traders using AI-powered signals
            </p>
            <Link
              href="/auth/register"
              className="inline-flex items-center justify-center w-full bg-white text-primary-600 font-semibold py-3 px-6 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Get Started Free
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Mobile Bottom Navigation */}
      <nav className="nav-mobile">
        <Link href="/" className="nav-item-mobile">
          <ChartBarIcon className="w-6 h-6 mb-1" />
          Home
        </Link>
        <Link href="/signals" className="nav-item-mobile">
          <BoltIcon className="w-6 h-6 mb-1" />
          Signals
        </Link>
        <Link href="/dashboard" className="nav-item-mobile">
          <DevicePhoneMobileIcon className="w-6 h-6 mb-1" />
          Dashboard
        </Link>
        <Link href="/profile" className="nav-item-mobile">
          <ShieldCheckIcon className="w-6 h-6 mb-1" />
          Profile
        </Link>
      </nav>
    </div>
  )
}

// Feature Card Component
function FeatureCard({
  icon,
  title,
  description
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="card-mobile flex items-start gap-4"
    >
      <div className="flex-shrink-0 w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center text-primary-600 dark:text-primary-400">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-dark-900 dark:text-white mb-1">
          {title}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {description}
        </p>
      </div>
    </motion.div>
  )
}