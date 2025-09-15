'use client';

import React, { memo, useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  Shield,
  Play,
  MoreVertical,
  Activity,
  AlertTriangle
} from 'lucide-react';
import { TradingSignal } from '../../types/trading';
import { useTouchGestures } from '../../hooks/useTouchGestures';
import {
  formatPrice,
  formatPercentage,
  formatTimeUntilExpiry,
  getStatusColor,
  getPnLColor,
  truncateText
} from '../../utils/formatters';

interface SignalCardProps {
  signal: TradingSignal;
  onExecute?: (signalId: string) => void;
  onToggleDetails?: (signalId: string) => void;
  isExpanded?: boolean;
  className?: string;
}

const SignalCard: React.FC<SignalCardProps> = memo(({
  signal,
  onExecute,
  onToggleDetails,
  isExpanded = false,
  className = ''
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [isPressed, setIsPressed] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const statusColor = getStatusColor(signal.status);
  const pnlColor = signal.pnl ? getPnLColor(signal.pnl) : '#cccccc';
  const isExpired = signal.status === 'expired';
  const canExecute = signal.status === 'active' && !isExpired;

  useTouchGestures(cardRef, {
    onTap: () => {
      if (onToggleDetails) {
        onToggleDetails(signal.id);
      }
    },
    onLongPress: () => {
      setShowActions(true);
    },
    onSwipeLeft: () => {
      if (canExecute && onExecute) {
        onExecute(signal.id);
      }
    }
  });

  useEffect(() => {
    if (showActions) {
      const timer = setTimeout(() => setShowActions(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [showActions]);

  const confidenceWidth = Math.min(Math.max(signal.confidence * 100, 0), 100);

  return (
    <motion.div
      ref={cardRef}
      className={`relative bg-gray-900 border border-gray-800 rounded-xl p-4 mb-3 transition-all duration-200 ${className}`}
      style={{
        borderLeftColor: statusColor,
        borderLeftWidth: '4px'
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{
        opacity: 1,
        y: 0,
        scale: isPressed ? 0.98 : 1,
        boxShadow: isPressed
          ? '0 4px 20px rgba(0, 255, 136, 0.2)'
          : '0 2px 10px rgba(0, 0, 0, 0.3)'
      }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
      onTouchStart={() => setIsPressed(true)}
      onTouchEnd={() => setIsPressed(false)}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="flex items-center">
            {signal.type === 'BUY' ? (
              <TrendingUp className="w-5 h-5 text-green-400" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-400" />
            )}
            <span className="ml-2 text-lg font-bold text-green-400">
              {signal.symbol}
            </span>
          </div>
          <span className="text-xs text-gray-400 max-w-24 truncate">
            {signal.instrumentName}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <div
            className="px-2 py-1 rounded text-xs font-medium border"
            style={{
              color: statusColor,
              borderColor: statusColor,
              backgroundColor: `${statusColor}15`
            }}
          >
            {signal.status.toUpperCase()}
          </div>

          <button
            onClick={() => setShowActions(!showActions)}
            className="p-1 text-gray-400 hover:text-white transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Price and Confidence */}
      <div className="grid grid-cols-3 gap-4 mb-3">
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">ENTRY</div>
          <div className="text-sm font-mono text-white">
            {formatPrice(signal.entryPrice)}
          </div>
        </div>

        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">CURRENT</div>
          <div className="text-sm font-mono text-blue-400">
            {formatPrice(signal.currentPrice)}
          </div>
        </div>

        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">CONFIDENCE</div>
          <div className="text-sm font-bold text-green-400">
            {formatPercentage(signal.confidence)}
          </div>
          <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
            <div
              className="bg-green-400 h-1 rounded-full transition-all duration-300"
              style={{ width: `${confidenceWidth}%` }}
            />
          </div>
        </div>
      </div>

      {/* Targets */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div className="flex items-center justify-between p-2 bg-gray-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <Shield className="w-3 h-3 text-red-400" />
            <span className="text-xs text-gray-400">STOP</span>
          </div>
          <span className="text-sm font-mono text-red-400">
            {formatPrice(signal.stopLoss)}
          </span>
        </div>

        <div className="flex items-center justify-between p-2 bg-gray-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <Target className="w-3 h-3 text-green-400" />
            <span className="text-xs text-gray-400">TARGET</span>
          </div>
          <span className="text-sm font-mono text-green-400">
            {formatPrice(signal.takeProfit)}
          </span>
        </div>
      </div>

      {/* Risk/Reward and PnL */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">R:R RATIO</div>
          <div className="text-sm font-bold text-yellow-400">
            1:{signal.riskRewardRatio.toFixed(2)}
          </div>
        </div>

        {signal.pnl !== undefined && (
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-1">P&L</div>
            <div
              className="text-sm font-bold"
              style={{ color: pnlColor }}
            >
              {signal.pnl > 0 ? '+' : ''}{signal.pnl.toFixed(2)}
            </div>
          </div>
        )}
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-700 pt-3 mt-3"
          >
            {/* Motivations */}
            {signal.motivations.length > 0 && (
              <div className="mb-3">
                <div className="text-xs text-gray-400 mb-2 flex items-center">
                  <Activity className="w-3 h-3 mr-1" />
                  ANALYSIS
                </div>
                <div className="space-y-1">
                  {signal.motivations.slice(0, 3).map((motivation, index) => (
                    <div key={index} className="text-xs text-gray-300 bg-gray-800 p-2 rounded">
                      {truncateText(motivation, 80)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Metrics */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xs text-gray-400">VOLUME</div>
                <div className="text-sm text-white">{signal.volume}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400">RISK</div>
                <div className="text-sm text-red-400">{signal.risk.toFixed(2)}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-400">REWARD</div>
                <div className="text-sm text-green-400">{signal.reward.toFixed(2)}%</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-700">
        <div className="text-xs text-gray-500 font-mono">
          #{signal.id.slice(-8)}
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <Clock className="w-3 h-3 text-yellow-400" />
          <span className="text-yellow-400 font-mono">
            {formatTimeUntilExpiry(signal.expiresAt)}
          </span>
        </div>
      </div>

      {/* Execute Button */}
      {canExecute && (
        <motion.button
          className="w-full mt-3 bg-green-500 hover:bg-green-600 text-black font-bold py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-all duration-200"
          whileTap={{ scale: 0.98 }}
          onClick={(e) => {
            e.stopPropagation();
            if (onExecute) onExecute(signal.id);
          }}
        >
          <Play className="w-4 h-4" />
          <span>EXECUTE TRADE</span>
        </motion.button>
      )}

      {/* Action Menu */}
      <AnimatePresence>
        {showActions && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute top-2 right-2 bg-gray-800 border border-gray-600 rounded-lg p-2 z-10 shadow-xl"
          >
            <div className="text-xs text-gray-300 space-y-1">
              <div>Swipe left to execute</div>
              <div>Tap to expand</div>
              <div>Long press for actions</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Real-time indicator */}
      {signal.isRealTime && (
        <div className="absolute top-2 left-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
        </div>
      )}

      {/* Expired overlay */}
      {isExpired && (
        <div className="absolute inset-0 bg-black bg-opacity-50 rounded-xl flex items-center justify-center">
          <div className="text-center">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <div className="text-red-400 font-bold">EXPIRED</div>
          </div>
        </div>
      )}
    </motion.div>
  );
});

SignalCard.displayName = 'SignalCard';

export default SignalCard;