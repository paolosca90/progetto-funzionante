'use client';

import React, { memo, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  Shield,
  BarChart3,
  Zap,
  Clock,
  Award,
  AlertTriangle,
  Percent
} from 'lucide-react';
import { MarketStats } from '../../types/trading';
import {
  formatCurrency,
  formatPercentage,
  formatNumber,
  getPnLColor
} from '../../utils/formatters';

interface StatsOverviewProps {
  stats: MarketStats;
  className?: string;
  layout?: 'grid' | 'horizontal';
  showAnimation?: boolean;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  color: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  isLoading?: boolean;
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = memo(({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
  trendValue,
  isLoading = false,
  onClick
}) => {
  const trendColor = trend === 'up' ? '#00ff88' : trend === 'down' ? '#ff4444' : '#666666';
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Activity;

  return (
    <motion.div
      className={`bg-gray-900 border border-gray-800 rounded-xl p-4 ${onClick ? 'cursor-pointer hover:border-gray-700' : ''} transition-all duration-200`}
      whileHover={onClick ? { scale: 1.02 } : {}}
      whileTap={onClick ? { scale: 0.98 } : {}}
      onClick={onClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div
            className="p-2 rounded-lg"
            style={{ backgroundColor: `${color}20` }}
          >
            <Icon className="w-4 h-4" style={{ color }} />
          </div>
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">
            {title}
          </span>
        </div>

        {trend && trendValue && (
          <div className="flex items-center space-x-1">
            <TrendIcon className="w-3 h-3" style={{ color: trendColor }} />
            <span className="text-xs font-mono" style={{ color: trendColor }}>
              {trendValue}
            </span>
          </div>
        )}
      </div>

      {/* Value */}
      <div className="mb-2">
        {isLoading ? (
          <div className="h-8 bg-gray-800 rounded animate-pulse" />
        ) : (
          <div className="text-2xl font-bold text-white">
            {typeof value === 'number' ? formatNumber(value) : value}
          </div>
        )}
      </div>

      {/* Subtitle */}
      {subtitle && (
        <div className="text-xs text-gray-500">
          {subtitle}
        </div>
      )}
    </motion.div>
  );
});

StatCard.displayName = 'StatCard';

const StatsOverview: React.FC<StatsOverviewProps> = memo(({
  stats,
  className = '',
  layout = 'grid',
  showAnimation = true
}) => {
  const pnlTrend = useMemo(() => {
    if (stats.dailyPnL > 0) return 'up';
    if (stats.dailyPnL < 0) return 'down';
    return 'neutral';
  }, [stats.dailyPnL]);

  const signalsTrend = useMemo(() => {
    if (stats.activeSignals > stats.totalSignals * 0.3) return 'up';
    if (stats.activeSignals < stats.totalSignals * 0.1) return 'down';
    return 'neutral';
  }, [stats.activeSignals, stats.totalSignals]);

  const gridCols = layout === 'grid' ? 'grid-cols-2 md:grid-cols-4' : 'grid-cols-1 md:grid-cols-6';

  const statsData = [
    {
      title: 'Total P&L',
      value: formatCurrency(stats.totalPnL),
      subtitle: `Daily: ${formatCurrency(stats.dailyPnL)}`,
      icon: DollarSign,
      color: getPnLColor(stats.totalPnL),
      trend: pnlTrend,
      trendValue: formatCurrency(stats.dailyPnL)
    },
    {
      title: 'Success Rate',
      value: formatPercentage(stats.successRate),
      subtitle: `${stats.totalSignals} total signals`,
      icon: Target,
      color: stats.successRate > 0.7 ? '#00ff88' : stats.successRate > 0.5 ? '#ffaa00' : '#ff4444',
      trend: stats.successRate > 0.6 ? 'up' : stats.successRate < 0.4 ? 'down' : 'neutral',
      trendValue: `${Math.round(stats.successRate * stats.totalSignals)} wins`
    },
    {
      title: 'Active Signals',
      value: stats.activeSignals,
      subtitle: `${formatPercentage(stats.activeSignals / stats.totalSignals)} of total`,
      icon: Activity,
      color: '#00ff88',
      trend: signalsTrend,
      trendValue: `${stats.activeSignals}/${stats.totalSignals}`
    },
    {
      title: 'Win Rate',
      value: formatPercentage(stats.winRate),
      subtitle: 'Last 30 days',
      icon: Award,
      color: stats.winRate > 0.6 ? '#00ff88' : '#ffaa00',
      trend: stats.winRate > 0.5 ? 'up' : 'down',
      trendValue: formatPercentage(stats.winRate - 0.5)
    },
    {
      title: 'Avg Risk',
      value: formatPercentage(stats.averageRisk),
      subtitle: `Reward: ${formatPercentage(stats.averageReward)}`,
      icon: Shield,
      color: stats.averageRisk < 0.02 ? '#00ff88' : stats.averageRisk < 0.05 ? '#ffaa00' : '#ff4444',
      trend: stats.averageRisk < 0.03 ? 'up' : 'down',
      trendValue: `R:R 1:${(stats.averageReward / stats.averageRisk).toFixed(1)}`
    },
    {
      title: 'Volume',
      value: formatNumber(stats.totalVolume, true),
      subtitle: 'Total traded',
      icon: BarChart3,
      color: '#6366f1',
      trend: 'neutral'
    }
  ];

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">Trading Stats</h2>
          <p className="text-sm text-gray-400">Real-time performance metrics</p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-xs text-gray-400">Live</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className={`grid ${gridCols} gap-4 mb-6`}>
        {statsData.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={showAnimation ? { opacity: 0, y: 20 } : {}}
            animate={showAnimation ? { opacity: 1, y: 0 } : {}}
            transition={showAnimation ? { duration: 0.3, delay: index * 0.1 } : {}}
          >
            <StatCard {...stat} />
          </motion.div>
        ))}
      </div>

      {/* Performance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Best Performer */}
        <motion.div
          className="bg-gray-900 border border-gray-800 rounded-xl p-4"
          initial={showAnimation ? { opacity: 0, x: -20 } : {}}
          animate={showAnimation ? { opacity: 1, x: 0 } : {}}
          transition={showAnimation ? { duration: 0.3, delay: 0.6 } : {}}
        >
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-2 bg-green-500 bg-opacity-20 rounded-lg">
              <TrendingUp className="w-4 h-4 text-green-400" />
            </div>
            <div>
              <div className="text-sm font-medium text-white">Best Performer</div>
              <div className="text-xs text-gray-400">This week</div>
            </div>
          </div>

          <div className="text-lg font-bold text-green-400 mb-1">
            {stats.bestPerformer || 'N/A'}
          </div>
          <div className="text-xs text-gray-500">
            Top performing signal
          </div>
        </motion.div>

        {/* Weekly P&L */}
        <motion.div
          className="bg-gray-900 border border-gray-800 rounded-xl p-4"
          initial={showAnimation ? { opacity: 0, x: 20 } : {}}
          animate={showAnimation ? { opacity: 1, x: 0 } : {}}
          transition={showAnimation ? { duration: 0.3, delay: 0.7 } : {}}
        >
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-2 bg-blue-500 bg-opacity-20 rounded-lg">
              <BarChart3 className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <div className="text-sm font-medium text-white">Weekly P&L</div>
              <div className="text-xs text-gray-400">Last 7 days</div>
            </div>
          </div>

          <div
            className="text-lg font-bold mb-1"
            style={{ color: getPnLColor(stats.weeklyPnL) }}
          >
            {formatCurrency(stats.weeklyPnL)}
          </div>
          <div className="text-xs text-gray-500">
            {stats.weeklyPnL > 0 ? 'Profit' : 'Loss'} this week
          </div>
        </motion.div>
      </div>

      {/* Risk Warning */}
      {stats.averageRisk > 0.05 && (
        <motion.div
          className="mt-4 bg-yellow-500 bg-opacity-10 border border-yellow-500 border-opacity-30 rounded-xl p-4"
          initial={showAnimation ? { opacity: 0, y: 20 } : {}}
          animate={showAnimation ? { opacity: 1, y: 0 } : {}}
          transition={showAnimation ? { duration: 0.3, delay: 0.8 } : {}}
        >
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <div>
              <div className="text-sm font-medium text-yellow-400">High Risk Detected</div>
              <div className="text-xs text-yellow-300 mt-1">
                Average risk per trade is {formatPercentage(stats.averageRisk)}.
                Consider reducing position sizes.
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
});

StatsOverview.displayName = 'StatsOverview';

export default StatsOverview;