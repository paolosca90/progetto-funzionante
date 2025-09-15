export const formatPrice = (price: number, decimals: number = 5): string => {
  return price.toFixed(decimals);
};

export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

export const formatNumber = (number: number, compact: boolean = false): string => {
  if (compact) {
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      compactDisplay: 'short',
    }).format(number);
  }

  return new Intl.NumberFormat('en-US').format(number);
};

export const formatTimeAgo = (timestamp: string): string => {
  const now = new Date();
  const time = new Date(timestamp);
  const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return `${diffInSeconds}s ago`;
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays}d ago`;
};

export const formatTimeUntilExpiry = (expiresAt: string): string => {
  const now = new Date();
  const expiry = new Date(expiresAt);
  const diffInSeconds = Math.floor((expiry.getTime() - now.getTime()) / 1000);

  if (diffInSeconds <= 0) {
    return 'EXPIRED';
  }

  if (diffInSeconds < 60) {
    return `${diffInSeconds}s`;
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours}h`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays}d`;
};

export const formatVolume = (volume: number): string => {
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(1)}M`;
  }
  if (volume >= 1000) {
    return `${(volume / 1000).toFixed(1)}K`;
  }
  return volume.toString();
};

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'active':
      return '#00ff88';
    case 'expired':
      return '#ff4444';
    case 'executed':
      return '#ffaa00';
    case 'cancelled':
      return '#666666';
    default:
      return '#cccccc';
  }
};

export const getPnLColor = (pnl: number): string => {
  if (pnl > 0) return '#00ff88';
  if (pnl < 0) return '#ff4444';
  return '#cccccc';
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
};