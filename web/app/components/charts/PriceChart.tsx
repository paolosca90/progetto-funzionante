'use client';

import React, { memo, useMemo, useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Bar
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Settings,
  Maximize2,
  Eye,
  EyeOff
} from 'lucide-react';
import { PriceData, TradingSignal, ChartTimeframe } from '../../types/trading';
import { useTouchGestures } from '../../hooks/useTouchGestures';
import { formatPrice, formatTimeAgo } from '../../utils/formatters';

interface PriceChartProps {
  data: PriceData[];
  signal?: TradingSignal;
  timeframe: ChartTimeframe;
  onTimeframeChange?: (timeframe: ChartTimeframe) => void;
  height?: number;
  className?: string;
  showVolume?: boolean;
  showGrid?: boolean;
  theme?: 'dark' | 'light';
}

const timeframes: ChartTimeframe[] = [
  { label: '1M', value: '1m', interval: 60000 },
  { label: '5M', value: '5m', interval: 300000 },
  { label: '15M', value: '15m', interval: 900000 },
  { label: '1H', value: '1h', interval: 3600000 },
  { label: '4H', value: '4h', interval: 14400000 },
  { label: '1D', value: '1d', interval: 86400000 }
];

const PriceChart: React.FC<PriceChartProps> = memo(({
  data,
  signal,
  timeframe,
  onTimeframeChange,
  height = 300,
  className = '',
  showVolume = true,
  showGrid = true,
  theme = 'dark'
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSignalLevels, setShowSignalLevels] = useState(true);
  const [crosshair, setCrosshair] = useState<{ x: number; y: number } | null>(null);

  const colors = useMemo(() => ({
    background: theme === 'dark' ? '#0a0a0a' : '#ffffff',
    text: theme === 'dark' ? '#ffffff' : '#000000',
    grid: theme === 'dark' ? '#333333' : '#e0e0e0',
    line: '#00ff88',
    volume: theme === 'dark' ? '#444444' : '#cccccc',
    buyLevel: '#00ff88',
    sellLevel: '#ff4444',
    stopLoss: '#ff4444',
    takeProfit: '#00ff88'
  }), [theme]);

  // Prepare chart data with volume
  const chartData = useMemo(() => {
    return data.map((item, index) => ({
      ...item,
      timestamp: item.timestamp,
      time: new Date(item.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      }),
      volumeHeight: showVolume ? Math.max(item.volume / Math.max(...data.map(d => d.volume)) * 100, 1) : 0
    }));
  }, [data, showVolume]);

  // Touch gestures for chart interaction
  useTouchGestures(chartRef, {
    onPinch: (scale) => {
      setZoomLevel(prev => Math.min(Math.max(prev * scale, 0.5), 3));
    },
    onSwipeUp: () => {
      if (onTimeframeChange) {
        const currentIndex = timeframes.findIndex(tf => tf.value === timeframe.value);
        if (currentIndex > 0) {
          onTimeframeChange(timeframes[currentIndex - 1]);
        }
      }
    },
    onSwipeDown: () => {
      if (onTimeframeChange) {
        const currentIndex = timeframes.findIndex(tf => tf.value === timeframe.value);
        if (currentIndex < timeframes.length - 1) {
          onTimeframeChange(timeframes[currentIndex + 1]);
        }
      }
    },
    onTap: (event) => {
      const rect = chartRef.current?.getBoundingClientRect();
      if (rect) {
        setCrosshair({
          x: event.touches[0].clientX - rect.left,
          y: event.touches[0].clientY - rect.top
        });
        setTimeout(() => setCrosshair(null), 2000);
      }
    }
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = payload[0].payload;

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl"
      >
        <div className="text-xs text-gray-400 mb-2">{data.time}</div>
        <div className="space-y-1">
          <div className="flex justify-between space-x-4">
            <span className="text-xs text-gray-400">O:</span>
            <span className="text-xs text-white font-mono">{formatPrice(data.open)}</span>
          </div>
          <div className="flex justify-between space-x-4">
            <span className="text-xs text-gray-400">H:</span>
            <span className="text-xs text-green-400 font-mono">{formatPrice(data.high)}</span>
          </div>
          <div className="flex justify-between space-x-4">
            <span className="text-xs text-gray-400">L:</span>
            <span className="text-xs text-red-400 font-mono">{formatPrice(data.low)}</span>
          </div>
          <div className="flex justify-between space-x-4">
            <span className="text-xs text-gray-400">C:</span>
            <span className="text-xs text-white font-mono">{formatPrice(data.close)}</span>
          </div>
          {showVolume && (
            <div className="flex justify-between space-x-4">
              <span className="text-xs text-gray-400">V:</span>
              <span className="text-xs text-blue-400 font-mono">{data.volume.toLocaleString()}</span>
            </div>
          )}
        </div>
      </motion.div>
    );
  };

  const currentPrice = data.length > 0 ? data[data.length - 1].close : 0;
  const priceChange = data.length > 1 ? currentPrice - data[data.length - 2].close : 0;
  const priceChangePercent = data.length > 1 ? (priceChange / data[data.length - 2].close) * 100 : 0;

  return (
    <div
      ref={chartRef}
      className={`relative bg-gray-900 rounded-xl border border-gray-800 ${className}`}
      style={{ height: isFullscreen ? '100vh' : height }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {priceChange >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-400" />
            )}
            <span className="text-lg font-bold text-white">
              {formatPrice(currentPrice)}
            </span>
          </div>

          <div className={`text-sm ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {priceChange >= 0 ? '+' : ''}{formatPrice(priceChange)}
            ({priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Timeframe selector */}
          <div className="flex bg-gray-800 rounded-lg p-1">
            {timeframes.map((tf) => (
              <button
                key={tf.value}
                onClick={() => onTimeframeChange?.(tf)}
                className={`px-2 py-1 text-xs rounded transition-all ${
                  tf.value === timeframe.value
                    ? 'bg-green-500 text-black font-bold'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          {/* Controls */}
          <div className="flex space-x-1">
            <button
              onClick={() => setShowSignalLevels(!showSignalLevels)}
              className="p-1 text-gray-400 hover:text-white transition-colors"
            >
              {showSignalLevels ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>

            <button
              onClick={() => setZoomLevel(1)}
              className="p-1 text-gray-400 hover:text-white transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1 text-gray-400 hover:text-white transition-colors"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Chart Container */}
      <div className="p-4" style={{ height: `calc(100% - 80px)` }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            {showGrid && (
              <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} opacity={0.3} />
            )}

            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: colors.text }}
              interval="preserveStartEnd"
            />

            <YAxis
              domain={['dataMin - 0.1', 'dataMax + 0.1']}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: colors.text }}
              tickFormatter={(value) => formatPrice(value)}
              width={60}
            />

            <Tooltip content={<CustomTooltip />} />

            {/* Volume bars */}
            {showVolume && (
              <Bar
                dataKey="volumeHeight"
                fill={colors.volume}
                opacity={0.3}
                yAxisId="volume"
              />
            )}

            {/* Price line */}
            <Line
              type="monotone"
              dataKey="close"
              stroke={colors.line}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: colors.line }}
            />

            {/* Signal levels */}
            {signal && showSignalLevels && (
              <>
                <ReferenceLine
                  y={signal.entryPrice}
                  stroke={signal.type === 'BUY' ? colors.buyLevel : colors.sellLevel}
                  strokeDasharray="5 5"
                  label={{ value: 'Entry', position: 'insideTopRight' }}
                />
                <ReferenceLine
                  y={signal.stopLoss}
                  stroke={colors.stopLoss}
                  strokeDasharray="3 3"
                  label={{ value: 'Stop Loss', position: 'insideTopRight' }}
                />
                <ReferenceLine
                  y={signal.takeProfit}
                  stroke={colors.takeProfit}
                  strokeDasharray="3 3"
                  label={{ value: 'Take Profit', position: 'insideTopRight' }}
                />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Crosshair */}
      <AnimatePresence>
        {crosshair && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute pointer-events-none"
            style={{
              left: crosshair.x,
              top: crosshair.y,
              transform: 'translate(-50%, -50%)'
            }}
          >
            <div className="w-px h-full bg-white opacity-50 absolute" />
            <div className="h-px w-full bg-white opacity-50 absolute" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Zoom indicator */}
      {zoomLevel !== 1 && (
        <div className="absolute bottom-4 left-4 bg-gray-800 px-2 py-1 rounded text-xs text-gray-400">
          Zoom: {(zoomLevel * 100).toFixed(0)}%
        </div>
      )}

      {/* Gesture hints */}
      <div className="absolute bottom-4 right-4 text-xs text-gray-500 space-y-1">
        <div>Pinch to zoom</div>
        <div>Swipe up/down to change timeframe</div>
        <div>Tap for crosshair</div>
      </div>
    </div>
  );
});

PriceChart.displayName = 'PriceChart';

export default PriceChart;