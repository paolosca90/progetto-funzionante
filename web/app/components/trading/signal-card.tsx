'use client'

import { memo, useMemo } from 'react'
import { motion } from 'framer-motion'
import { ArrowUpIcon, ArrowDownIcon, ClockIcon } from '@heroicons/react/24/outline'
import { formatDistanceToNow } from 'date-fns'

interface Signal {
  id: string
  symbol: string
  direction: 'BUY' | 'SELL'
  entryPrice: number
  stopLoss: number
  takeProfit: number
  confidence: number
  timeframe: string
  status: 'active' | 'closed' | 'pending'
  createdAt: string
}

interface SignalCardProps {
  signal: Signal
  onClick?: (signal: Signal) => void
  className?: string
}

const SignalCard = memo(function SignalCard({
  signal,
  onClick,
  className = ''
}: SignalCardProps) {
  // Memoize calculations to prevent unnecessary re-renders
  const {
    directionColor,
    confidenceColor,
    pipsToSL,
    pipsToTP,
    riskReward,
    timeAgo
  } = useMemo(() => {
    const directionColor = signal.direction === 'BUY'
      ? 'text-success-600 bg-success-50'
      : 'text-danger-600 bg-danger-50'

    const confidenceColor = signal.confidence >= 80
      ? 'text-success-600'
      : signal.confidence >= 60
        ? 'text-warning-600'
        : 'text-danger-600'

    const pipsToSL = Math.abs(signal.entryPrice - signal.stopLoss) * 10000
    const pipsToTP = Math.abs(signal.takeProfit - signal.entryPrice) * 10000
    const riskReward = (pipsToTP / pipsToSL).toFixed(1)

    const timeAgo = formatDistanceToNow(new Date(signal.createdAt), { addSuffix: true })

    return {
      directionColor,
      confidenceColor,
      pipsToSL: pipsToSL.toFixed(1),
      pipsToTP: pipsToTP.toFixed(1),
      riskReward,
      timeAgo
    }
  }, [signal.direction, signal.confidence, signal.entryPrice, signal.stopLoss, signal.takeProfit, signal.createdAt])

  const handleClick = useMemo(() => {
    if (!onClick) return undefined
    return () => onClick(signal)
  }, [onClick, signal])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileTap={{ scale: 0.98 }}
      className={`signal-card-mobile ${className}`}
      onClick={handleClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {/* Signal Header */}
      <div className="signal-header-mobile">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-dark-900 dark:text-white">
              {signal.symbol}
            </span>
            <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${directionColor}`}>
              {signal.direction === 'BUY' ? (
                <ArrowUpIcon className="w-3 h-3" />
              ) : (
                <ArrowDownIcon className="w-3 h-3" />
              )}
              {signal.direction}
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className={`text-sm font-semibold ${confidenceColor}`}>
            {signal.confidence}% confidence
          </div>
          <div className="signal-meta-mobile">
            <ClockIcon className="w-3 h-3" />
            {timeAgo}
          </div>
        </div>
      </div>

      {/* Price Information */}
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400 block">Entry</span>
          <span className="signal-price-mobile text-dark-900 dark:text-white">
            {signal.entryPrice.toFixed(5)}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400 block">Stop Loss</span>
          <span className="signal-price-mobile text-danger-600">
            {signal.stopLoss.toFixed(5)}
          </span>
          <span className="text-xs text-gray-500 block">-{pipsToSL} pips</span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400 block">Take Profit</span>
          <span className="signal-price-mobile text-success-600">
            {signal.takeProfit.toFixed(5)}
          </span>
          <span className="text-xs text-gray-500 block">+{pipsToTP} pips</span>
        </div>
      </div>

      {/* Signal Meta */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-4">
          <span>Timeframe: {signal.timeframe}</span>
          <span>R:R {riskReward}</span>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
          signal.status === 'active'
            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
            : signal.status === 'closed'
              ? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
              : 'bg-warning-100 text-warning-700 dark:bg-warning-900 dark:text-warning-300'
        }`}>
          {signal.status}
        </div>
      </div>
    </motion.div>
  )
})

export { SignalCard }
export type { Signal, SignalCardProps }