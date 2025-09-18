# SDK Examples for AI Trading System API

This document provides comprehensive SDK examples for various programming languages and use cases.

## Table of Contents

1. [Python SDK](#python-sdk)
2. [JavaScript/Node.js SDK](#javascriptnodejs-sdk)
3. [cURL Examples](#curl-examples)
4. [Advanced Examples](#advanced-examples)
5. [Integration Examples](#integration-examples)
6. [Testing Examples](#testing-examples)

## Python SDK

### Installation

```bash
pip install requests python-dotenv
```

### Basic SDK Class

```python
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import time

class TradingSignalsSDK:
    """
    Python SDK for AI Trading System API
    """

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    def authenticate(self) -> bool:
        """Authenticate with the API and get access token"""
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data={
                    "username": self.username,
                    "password": self.password
                },
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.refresh_token = token_data["refresh_token"]
                self.token_expires_at = datetime.now() + timedelta(minutes=30)
                return True
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/token/refresh",
                json={"refresh_token": self.refresh_token},
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.token_expires_at = datetime.now() + timedelta(minutes=30)
                return True
            else:
                print(f"Token refresh failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"Token refresh error: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        # Check if token needs refresh
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            if not self.refresh_access_token():
                raise Exception("Unable to refresh access token")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_latest_signals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest trading signals"""
        try:
            response = requests.get(
                f"{self.base_url}/api/signals/latest",
                headers=self.get_headers(),
                params={"limit": limit},
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get signals: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"Error getting signals: {e}")
            return []

    def create_signal(self, signal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new trading signal"""
        try:
            response = requests.post(
                f"{self.base_url}/signals/",
                headers=self.get_headers(),
                json=signal_data,
                timeout=30
            )

            if response.status_code == 201:
                return response.json()
            else:
                print(f"Failed to create signal: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error creating signal: {e}")
            return None

    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data for a symbol"""
        try:
            response = requests.get(
                f"{self.base_url}/api/oanda/market-data/{symbol}",
                headers=self.get_headers(),
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get market data: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error getting market data: {e}")
            return None

    def connect_oanda_account(self, account_id: str, environment: str = "demo") -> bool:
        """Connect OANDA account"""
        try:
            response = requests.post(
                f"{self.base_url}/api/oanda/connect",
                headers=self.get_headers(),
                data={
                    "account_id": account_id,
                    "environment": environment
                },
                timeout=30
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Error connecting OANDA account: {e}")
            return False

    def generate_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate signal for a specific symbol"""
        try:
            response = requests.post(
                f"{self.base_url}/api/signals/generate/{symbol}",
                headers=self.get_headers(),
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to generate signal: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error generating signal: {e}")
            return None

    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get current user profile"""
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.get_headers(),
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get user profile: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

    def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """Get user dashboard data"""
        try:
            response = requests.get(
                f"{self.base_url}/users/dashboard",
                headers=self.get_headers(),
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get dashboard data: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return None
```

### Advanced Trading Bot Example

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional

class AdvancedTradingBot:
    """
    Advanced trading bot with signal analysis and risk management
    """

    def __init__(self, sdk: TradingSignalsSDK, config: Dict[str, Any]):
        self.sdk = sdk
        self.config = config
        self.positions = {}
        self.performance_history = []

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze signals and filter based on criteria"""
        analyzed_signals = []

        for signal in signals:
            # Apply filters
            if self._passes_filters(signal):
                # Calculate risk score
                risk_score = self._calculate_risk_score(signal)

                # Add analysis to signal
                signal['analysis'] = {
                    'risk_score': risk_score,
                    'recommended_position_size': self._calculate_position_size(signal),
                    'entry_timing': self._assess_entry_timing(signal),
                    'confidence_adjustment': self._adjust_confidence(signal)
                }

                analyzed_signals.append(signal)

        return sorted(analyzed_signals, key=lambda x: x['analysis']['risk_score'], reverse=True)

    def _passes_filters(self, signal: Dict[str, Any]) -> bool:
        """Check if signal passes all filters"""
        filters = self.config.get('filters', {})

        # Minimum reliability filter
        if signal['reliability'] < filters.get('min_reliability', 70):
            return False

        # Risk level filter
        if filters.get('max_risk_level') and signal['risk_level'] == 'HIGH':
            return False

        # Symbol filter
        allowed_symbols = filters.get('allowed_symbols')
        if allowed_symbols and signal['symbol'] not in allowed_symbols:
            return False

        return True

    def _calculate_risk_score(self, signal: Dict[str, Any]) -> float:
        """Calculate risk score for signal"""
        reliability_score = signal['reliability'] / 100.0
        confidence_score = signal['confidence_score'] / 100.0

        # Adjust based on risk level
        risk_multiplier = {
            'LOW': 1.2,
            'MEDIUM': 1.0,
            'HIGH': 0.8
        }.get(signal['risk_level'], 1.0)

        # Calculate technical score if available
        technical_score = 0.5
        if signal.get('rsi'):
            if signal['rsi'] < 30 or signal['rsi'] > 70:
                technical_score = 0.7

        return (reliability_score * 0.4 + confidence_score * 0.3 + technical_score * 0.3) * risk_multiplier

    def _calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate recommended position size"""
        account_balance = self.config.get('account_balance', 10000)
        risk_per_trade = self.config.get('risk_per_trade', 0.02)  # 2% risk

        # Calculate stop loss distance
        if signal['stop_loss'] and signal['entry_price']:
            stop_distance = abs(signal['entry_price'] - signal['stop_loss'])

            # Calculate risk amount
            risk_amount = account_balance * risk_per_trade

            # Calculate position size
            position_size = risk_amount / stop_distance

            # Apply maximum position size limit
            max_position = self.config.get('max_position_size', 0.1)
            return min(position_size, max_position)

        return 0.01  # Default position size

    def _assess_entry_timing(self, signal: Dict[str, Any]) -> str:
        """Assess entry timing for the signal"""
        # Simple timing assessment based on market session
        hour = datetime.now().hour

        if 8 <= hour <= 16:  # Market hours
            return "GOOD"
        elif 6 <= hour <= 8 or 16 <= hour <= 18:  # Extended hours
            return "FAIR"
        else:  # Off hours
            return "POOR"

    def _adjust_confidence(self, signal: Dict[str, Any]) -> float:
        """Adjust confidence based on market conditions"""
        base_confidence = signal['confidence_score']

        # Adjust based on market volatility
        if signal.get('volatility'):
            if signal['volatility'] > 0.02:  # High volatility
                base_confidence *= 0.9
            elif signal['volatility'] < 0.005:  # Low volatility
                base_confidence *= 1.1

        # Adjust based on spread
        if signal.get('spread'):
            if signal['spread'] > 0.001:  # High spread
                base_confidence *= 0.95

        return min(base_confidence, 100.0)

    def execute_signal(self, signal: Dict[str, Any]) -> bool:
        """Execute a trading signal"""
        try:
            analysis = signal['analysis']

            # Get current market data
            market_data = self.sdk.get_market_data(signal['symbol'])
            if not market_data:
                self.logger.error(f"Failed to get market data for {signal['symbol']}")
                return False

            # Check if entry price is still valid
            current_price = (market_data['bid'] + market_data['ask']) / 2
            price_deviation = abs(current_price - signal['entry_price']) / signal['entry_price']

            if price_deviation > 0.01:  # 1% deviation
                self.logger.warning(f"Entry price deviated by {price_deviation:.2%}")
                return False

            # Execute trade
            execution_result = self._execute_trade(signal, market_data, analysis)

            if execution_result:
                self.logger.info(f"Successfully executed {signal['symbol']} {signal['signal_type']}")
                return True
            else:
                self.logger.error(f"Failed to execute {signal['symbol']} {signal['signal_type']}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            return False

    def _execute_trade(self, signal: Dict[str, Any], market_data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Execute the actual trade"""
        # This is a placeholder for actual trade execution
        # In a real implementation, this would integrate with your trading platform

        position_size = analysis['recommended_position_size']
        entry_price = market_data['ask'] if signal['signal_type'] == 'BUY' else market_data['bid']

        # Record position
        position = {
            'symbol': signal['symbol'],
            'type': signal['signal_type'],
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'entry_time': datetime.now(),
            'signal_id': signal['id'],
            'initial_risk': abs(entry_price - signal['stop_loss']) * position_size
        }

        self.positions[signal['symbol']] = position
        self.logger.info(f"Position opened: {position}")

        return True

    def monitor_positions(self):
        """Monitor open positions and manage exits"""
        for symbol, position in self.positions.items():
            try:
                # Get current market data
                market_data = self.sdk.get_market_data(symbol)
                if not market_data:
                    continue

                current_price = (market_data['bid'] + market_data['ask']) / 2
                unrealized_pnl = self._calculate_unrealized_pnl(position, current_price)

                # Check exit conditions
                should_exit = self._should_exit_position(position, current_price, unrealized_pnl)

                if should_exit:
                    exit_price = market_data['bid'] if position['type'] == 'BUY' else market_data['ask']
                    self._close_position(position, exit_price, unrealized_pnl)

            except Exception as e:
                self.logger.error(f"Error monitoring position {symbol}: {e}")

    def _calculate_unrealized_pnl(self, position: Dict[str, Any], current_price: float) -> float:
        """Calculate unrealized P&L for a position"""
        if position['type'] == 'BUY':
            return (current_price - position['entry_price']) * position['position_size']
        else:
            return (position['entry_price'] - current_price) * position['position_size']

    def _should_exit_position(self, position: Dict[str, Any], current_price: float, unrealized_pnl: float) -> bool:
        """Determine if a position should be closed"""
        # Check stop loss
        if position['type'] == 'BUY' and current_price <= position['stop_loss']:
            return True
        elif position['type'] == 'SELL' and current_price >= position['stop_loss']:
            return True

        # Check take profit
        if position['take_profit'] and position['type'] == 'BUY' and current_price >= position['take_profit']:
            return True
        elif position['take_profit'] and position['type'] == 'SELL' and current_price <= position['take_profit']:
            return True

        # Check time-based exit
        time_held = datetime.now() - position['entry_time']
        if time_held.total_seconds() > self.config.get('max_trade_duration', 86400):  # 24 hours
            return True

        # Check risk-based exit
        if unrealized_pnl < -position['initial_risk'] * 2:  # 2x initial risk
            return True

        return False

    def _close_position(self, position: Dict[str, Any], exit_price: float, unrealized_pnl: float):
        """Close a position and record performance"""
        # Calculate realized P&L
        realized_pnl = unrealized_pnl

        # Calculate trade duration
        trade_duration = datetime.now() - position['entry_time']

        # Record performance
        performance_record = {
            'symbol': position['symbol'],
            'type': position['type'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'position_size': position['position_size'],
            'realized_pnl': realized_pnl,
            'trade_duration': trade_duration.total_seconds(),
            'exit_reason': self._determine_exit_reason(position, exit_price),
            'exit_time': datetime.now()
        }

        self.performance_history.append(performance_record)

        # Remove from positions
        del self.positions[position['symbol']]

        self.logger.info(f"Position closed: {performance_record}")

    def _determine_exit_reason(self, position: Dict[str, Any], exit_price: float) -> str:
        """Determine the reason for position exit"""
        if position['type'] == 'BUY':
            if exit_price <= position['stop_loss']:
                return 'STOP_LOSS'
            elif position['take_profit'] and exit_price >= position['take_profit']:
                return 'TAKE_PROFIT'
        else:
            if exit_price >= position['stop_loss']:
                return 'STOP_LOSS'
            elif position['take_profit'] and exit_price <= position['take_profit']:
                return 'TAKE_PROFIT'

        return 'TIME_OR_RISK_BASED'

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not self.performance_history:
            return {}

        df = pd.DataFrame(self.performance_history)

        metrics = {
            'total_trades': len(df),
            'winning_trades': len(df[df['realized_pnl'] > 0]),
            'losing_trades': len(df[df['realized_pnl'] < 0]),
            'win_rate': len(df[df['realized_pnl'] > 0]) / len(df) if len(df) > 0 else 0,
            'total_pnl': df['realized_pnl'].sum(),
            'average_pnl': df['realized_pnl'].mean(),
            'max_win': df['realized_pnl'].max(),
            'max_loss': df['realized_pnl'].min(),
            'average_trade_duration': df['trade_duration'].mean() / 3600,  # Convert to hours
            'profit_factor': abs(df[df['realized_pnl'] > 0]['realized_pnl'].sum() / df[df['realized_pnl'] < 0]['realized_pnl'].sum()) if len(df[df['realized_pnl'] < 0]) > 0 else 0
        }

        return metrics

    def run_trading_loop(self):
        """Main trading loop"""
        self.logger.info("Starting advanced trading bot...")

        try:
            while True:
                # Get latest signals
                signals = self.sdk.get_latest_signals(limit=20)

                if signals:
                    # Analyze signals
                    analyzed_signals = self.analyze_signals(signals)

                    # Execute best signals
                    for signal in analyzed_signals[:3]:  # Top 3 signals
                        if signal['symbol'] not in self.positions:
                            self.execute_signal(signal)

                # Monitor existing positions
                self.monitor_positions()

                # Log performance
                metrics = self.get_performance_metrics()
                if metrics:
                    self.logger.info(f"Performance: Win Rate {metrics['win_rate']:.2%}, Total P&L ${metrics['total_pnl']:.2f}")

                # Wait for next iteration
                time.sleep(self.config.get('check_interval', 300))  # 5 minutes default

        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped by user")
        except Exception as e:
            self.logger.error(f"Trading bot error: {e}")

# Usage example
if __name__ == "__main__":
    # Initialize SDK
    sdk = TradingSignalsSDK(
        base_url="https://your-api-domain.com",
        username="your_username",
        password="your_password"
    )

    # Authenticate
    if sdk.authenticate():
        # Configure trading bot
        config = {
            'account_balance': 10000,
            'risk_per_trade': 0.02,
            'max_position_size': 0.1,
            'max_trade_duration': 86400,
            'check_interval': 300,
            'filters': {
                'min_reliability': 75,
                'max_risk_level': 'MEDIUM',
                'allowed_symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'GOLD']
            }
        }

        # Create and run trading bot
        bot = AdvancedTradingBot(sdk, config)
        bot.run_trading_loop()
```

## JavaScript/Node.js SDK

### Basic SDK Class

```javascript
class TradingSignalsSDK {
    constructor(baseUrl, username, password) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.username = username;
        this.password = password;
        this.accessToken = null;
        this.refreshToken = null;
        this.tokenExpiresAt = null;
    }

    async authenticate() {
        try {
            const response = await fetch(`${this.baseUrl}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `username=${encodeURIComponent(this.username)}&password=${encodeURIComponent(this.password)}`
            });

            if (response.ok) {
                const tokenData = await response.json();
                this.accessToken = tokenData.access_token;
                this.refreshToken = tokenData.refresh_token;
                this.tokenExpiresAt = new Date(Date.now() + 30 * 60 * 1000); // 30 minutes
                return true;
            } else {
                console.error('Authentication failed:', response.status, await response.text());
                return false;
            }
        } catch (error) {
            console.error('Authentication error:', error);
            return false;
        }
    }

    async refreshAccessToken() {
        if (!this.refreshToken) return false;

        try {
            const response = await fetch(`${this.baseUrl}/token/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            if (response.ok) {
                const tokenData = await response.json();
                this.accessToken = tokenData.access_token;
                this.tokenExpiresAt = new Date(Date.now() + 30 * 60 * 1000);
                return true;
            } else {
                console.error('Token refresh failed:', response.status, await response.text());
                return false;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }

    async getHeaders() {
        // Check if token needs refresh
        if (this.tokenExpiresAt && new Date() >= this.tokenExpiresAt) {
            await this.refreshAccessToken();
        }

        return {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
        };
    }

    async getLatestSignals(limit = 10) {
        try {
            const headers = await this.getHeaders();
            const response = await fetch(`${this.baseUrl}/api/signals/latest?limit=${limit}`, {
                headers
            });

            if (response.ok) {
                return await response.json();
            } else {
                console.error('Failed to get signals:', response.status, await response.text());
                return [];
            }
        } catch (error) {
            console.error('Error getting signals:', error);
            return [];
        }
    }

    async createSignal(signalData) {
        try {
            const headers = await this.getHeaders();
            const response = await fetch(`${this.baseUrl}/signals/`, {
                method: 'POST',
                headers,
                body: JSON.stringify(signalData)
            });

            if (response.ok) {
                return await response.json();
            } else {
                console.error('Failed to create signal:', response.status, await response.text());
                return null;
            }
        } catch (error) {
            console.error('Error creating signal:', error);
            return null;
        }
    }

    async getMarketData(symbol) {
        try {
            const headers = await this.getHeaders();
            const response = await fetch(`${this.baseUrl}/api/oanda/market-data/${symbol}`, {
                headers
            });

            if (response.ok) {
                return await response.json();
            } else {
                console.error('Failed to get market data:', response.status, await response.text());
                return null;
            }
        } catch (error) {
            console.error('Error getting market data:', error);
            return null;
        }
    }

    async generateSignal(symbol) {
        try {
            const headers = await this.getHeaders();
            const response = await fetch(`${this.baseUrl}/api/signals/generate/${symbol}`, {
                method: 'POST',
                headers
            });

            if (response.ok) {
                return await response.json();
            } else {
                console.error('Failed to generate signal:', response.status, await response.text());
                return null;
            }
        } catch (error) {
            console.error('Error generating signal:', error);
            return null;
        }
    }

    async getUserProfile() {
        try {
            const headers = await this.getHeaders();
            const response = await fetch(`${this.baseUrl}/users/me`, {
                headers
            });

            if (response.ok) {
                return await response.json();
            } else {
                console.error('Failed to get user profile:', response.status, await response.text());
                return null;
            }
        } catch (error) {
            console.error('Error getting user profile:', error);
            return null;
        }
    }
}

// Usage example
async function main() {
    const sdk = new TradingSignalsSDK(
        'https://your-api-domain.com',
        'your_username',
        'your_password'
    );

    // Authenticate
    if (await sdk.authenticate()) {
        console.log('✓ Authentication successful');

        // Get latest signals
        const signals = await sdk.getLatestSignals(5);
        console.log('Latest signals:', signals);

        // Get user profile
        const profile = await sdk.getUserProfile();
        console.log('User profile:', profile);

        // Get market data
        const marketData = await sdk.getMarketData('EURUSD');
        console.log('Market data:', marketData);

        // Generate a signal
        const generatedSignal = await sdk.generateSignal('EURUSD');
        console.log('Generated signal:', generatedSignal);
    }
}

main().catch(console.error);
```

### React Hook for Trading Signals

```javascript
import { useState, useEffect, useCallback } from 'react';

const useTradingSignals = (sdk) => {
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [userProfile, setUserProfile] = useState(null);

    // Get latest signals
    const getLatestSignals = useCallback(async (limit = 10) => {
        setLoading(true);
        setError(null);

        try {
            const latestSignals = await sdk.getLatestSignals(limit);
            setSignals(latestSignals);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [sdk]);

    // Get user profile
    const getUserProfile = useCallback(async () => {
        try {
            const profile = await sdk.getUserProfile();
            setUserProfile(profile);
        } catch (err) {
            setError(err.message);
        }
    }, [sdk]);

    // Create signal
    const createSignal = useCallback(async (signalData) => {
        setLoading(true);
        setError(null);

        try {
            const createdSignal = await sdk.createSignal(signalData);
            setSignals(prev => [createdSignal.signal, ...prev]);
            return createdSignal;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, [sdk]);

    // Get market data
    const getMarketData = useCallback(async (symbol) => {
        try {
            return await sdk.getMarketData(symbol);
        } catch (err) {
            setError(err.message);
            return null;
        }
    }, [sdk]);

    // Initialize
    useEffect(() => {
        getLatestSignals();
        getUserProfile();
    }, [getLatestSignals, getUserProfile]);

    return {
        signals,
        loading,
        error,
        userProfile,
        getLatestSignals,
        getUserProfile,
        createSignal,
        getMarketData
    };
};

// Usage in React component
const TradingDashboard = () => {
    const sdk = new TradingSignalsSDK(
        'https://your-api-domain.com',
        'your_username',
        'your_password'
    );

    const {
        signals,
        loading,
        error,
        userProfile,
        getLatestSignals,
        createSignal,
        getMarketData
    } = useTradingSignals(sdk);

    const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
    const [marketData, setMarketData] = useState(null);

    useEffect(() => {
        // Get market data for selected symbol
        if (selectedSymbol) {
            getMarketData(selectedSymbol).then(data => setMarketData(data));
        }
    }, [selectedSymbol, getMarketData]);

    const handleCreateSignal = async (signalData) => {
        const result = await createSignal(signalData);
        if (result) {
            alert('Signal created successfully!');
        }
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div className="trading-dashboard">
            <div className="user-info">
                <h2>Welcome, {userProfile?.username}</h2>
                <p>Subscription: {userProfile?.subscription_active ? 'Active' : 'Inactive'}</p>
            </div>

            <div className="market-data">
                <h3>Market Data</h3>
                <select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)}>
                    <option value="EURUSD">EUR/USD</option>
                    <option value="GBPUSD">GBP/USD</option>
                    <option value="USDJPY">USD/JPY</option>
                    <option value="GOLD">GOLD</option>
                </select>

                {marketData && (
                    <div className="data-display">
                        <p>Symbol: {marketData.symbol}</p>
                        <p>Bid: {marketData.bid}</p>
                        <p>Ask: {marketData.ask}</p>
                        <p>Spread: {marketData.spread}</p>
                    </div>
                )}
            </div>

            <div className="signals-section">
                <h3>Latest Signals</h3>
                <div className="signals-list">
                    {signals.map(signal => (
                        <div key={signal.id} className="signal-card">
                            <div className="signal-header">
                                <span className="symbol">{signal.symbol}</span>
                                <span className={`signal-type ${signal.signal_type.toLowerCase()}`}>
                                    {signal.signal_type}
                                </span>
                            </div>
                            <div className="signal-details">
                                <p>Entry: {signal.entry_price}</p>
                                <p>Stop Loss: {signal.stop_loss}</p>
                                <p>Take Profit: {signal.take_profit}</p>
                                <p>Reliability: {signal.reliability}%</p>
                            </div>
                            <div className="signal-analysis">
                                <p>AI Analysis: {signal.ai_analysis}</p>
                                <p>Risk Level: {signal.risk_level}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default TradingDashboard;
```

## cURL Examples

### Authentication

```bash
# Get access token
curl -X POST "https://your-api-domain.com/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Get Latest Signals

```bash
# Get latest signals
curl -X GET "https://your-api-domain.com/api/signals/latest?limit=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Create Signal

```bash
# Create a new signal
curl -X POST "https://your-api-domain.com/signals/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "reliability": 85.5,
    "ai_analysis": "Technical analysis shows bullish momentum",
    "confidence_score": 87.2,
    "risk_level": "MEDIUM"
  }'
```

### Get Market Data

```bash
# Get market data for EURUSD
curl -X GET "https://your-api-domain.com/api/oanda/market-data/EURUSD" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Generate Signal

```bash
# Generate signal for specific symbol
curl -X POST "https://your-api-domain.com/api/signals/generate/EURUSD" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Connect OANDA Account

```bash
# Connect OANDA account
curl -X POST "https://your-api-domain.com/api/oanda/connect" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "account_id=123-456-789012-001&environment=demo"
```

### Health Check

```bash
# Check system health
curl -X GET "https://your-api-domain.com/health/detailed" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### User Profile

```bash
# Get user profile
curl -X GET "https://your-api-domain.com/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

## Advanced Examples

### Automated Signal Processing Pipeline

```python
import asyncio
import aiohttp
from datetime import datetime, timedelta
import json

class AsyncTradingPipeline:
    def __init__(self, config):
        self.config = config
        self.session = None
        self.access_token = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authenticate(self):
        """Authenticate with the API"""
        auth_data = {
            'username': self.config['username'],
            'password': self.config['password']
        }

        async with self.session.post(
            f"{self.config['base_url']}/token",
            data=auth_data
        ) as response:
            if response.status == 200:
                token_data = await response.json()
                self.access_token = token_data['access_token']
                return True
            else:
                print(f"Authentication failed: {response.status}")
                return False

    async def get_headers(self):
        """Get request headers with authentication"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    async def get_signals_batch(self, symbols):
        """Get signals for multiple symbols concurrently"""
        tasks = []
        for symbol in symbols:
            task = self.get_signals_for_symbol(symbol)
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def get_signals_for_symbol(self, symbol):
        """Get signals for a specific symbol"""
        params = {'symbol': symbol, 'limit': 10}

        async with self.session.get(
            f"{self.config['base_url']}/signals/by-symbol/{symbol}",
            headers=await self.get_headers(),
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error getting signals for {symbol}: {response.status}")
                return []

    async def process_signals(self, signals_data):
        """Process signals and make trading decisions"""
        all_signals = []
        for signals in signals_data:
            if isinstance(signals, list):
                all_signals.extend(signals)

        # Filter and sort signals
        filtered_signals = [
            signal for signal in all_signals
            if signal['reliability'] >= self.config['min_reliability']
        ]

        sorted_signals = sorted(
            filtered_signals,
            key=lambda x: x['reliability'],
            reverse=True
        )

        return sorted_signals[:self.config['max_signals']]

    async def execute_trades(self, signals):
        """Execute trades based on signals"""
        trades = []

        for signal in signals:
            trade = await self.execute_trade(signal)
            if trade:
                trades.append(trade)

        return trades

    async def execute_trade(self, signal):
        """Execute a single trade"""
        trade_data = {
            'signal_id': signal['id'],
            'symbol': signal['symbol'],
            'signal_type': signal['signal_type'],
            'entry_price': signal['entry_price'],
            'position_size': self.config['position_size'],
            'execution_type': 'AUTO'
        }

        async with self.session.post(
            f"{self.config['base_url']}/trades/execute",
            headers=await self.get_headers(),
            json=trade_data
        ) as response:
            if response.status == 201:
                return await response.json()
            else:
                print(f"Trade execution failed: {response.status}")
                return None

    async def run_pipeline(self):
        """Run the complete trading pipeline"""
        print("Starting trading pipeline...")

        try:
            # Get signals for all symbols
            symbols = self.config['symbols']
            signals_data = await self.get_signals_batch(symbols)

            # Process signals
            processed_signals = await self.process_signals(signals_data)

            print(f"Processed {len(processed_signals)} signals")

            # Execute trades
            trades = await self.execute_trades(processed_signals)

            print(f"Executed {len(trades)} trades")

            return {
                'signals_processed': len(processed_signals),
                'trades_executed': len(trades),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Pipeline error: {e}")
            return {'error': str(e)}

# Usage example
async def main():
    config = {
        'base_url': 'https://your-api-domain.com',
        'username': 'your_username',
        'password': 'your_password',
        'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'GOLD'],
        'min_reliability': 75,
        'max_signals': 5,
        'position_size': 0.01
    }

    async with AsyncTradingPipeline(config) as pipeline:
        result = await pipeline.run_pipeline()
        print("Pipeline result:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Integration Examples

### Django Integration

```python
# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from trading_sdk import TradingSignalsSDK

# Initialize SDK
sdk = TradingSignalsSDK(
    base_url="https://your-api-domain.com",
    username="your_username",
    password="your_password"
)

@csrf_exempt
@require_http_methods(["GET"])
def dashboard_api(request):
    """Dashboard API endpoint"""
    if not sdk.access_token:
        sdk.authenticate()

    # Get user data
    user_profile = sdk.get_user_profile()
    latest_signals = sdk.get_latest_signals(limit=10)
    dashboard_data = sdk.get_dashboard_data()

    return JsonResponse({
        'user': user_profile,
        'signals': latest_signals,
        'dashboard': dashboard_data
    })

@csrf_exempt
@require_http_methods(["POST"])
def create_signal_api(request):
    """Create signal API endpoint"""
    if not sdk.access_token:
        sdk.authenticate()

    try:
        signal_data = json.loads(request.body)
        created_signal = sdk.create_signal(signal_data)

        if created_signal:
            return JsonResponse({
                'success': True,
                'signal': created_signal
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to create signal'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def trading_view(request):
    """Trading dashboard view"""
    return render(request, 'trading/dashboard.html')
```

### Flask Integration

```python
# app.py
from flask import Flask, render_template, request, jsonify
import json

from trading_sdk import TradingSignalsSDK

app = Flask(__name__)

# Initialize SDK
sdk = TradingSignalsSDK(
    base_url="https://your-api-domain.com",
    username="your_username",
    password="your_password"
)

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/signals')
def get_signals():
    """Get signals API endpoint"""
    limit = request.args.get('limit', 10, type=int)

    if not sdk.access_token:
        sdk.authenticate()

    signals = sdk.get_latest_signals(limit=limit)
    return jsonify(signals)

@app.route('/api/market-data/<symbol>')
def get_market_data(symbol):
    """Get market data API endpoint"""
    if not sdk.access_token:
        sdk.authenticate()

    market_data = sdk.get_market_data(symbol)
    return jsonify(market_data)

@app.route('/api/create-signal', methods=['POST'])
def create_signal():
    """Create signal API endpoint"""
    if not sdk.access_token:
        sdk.authenticate()

    try:
        signal_data = request.get_json()
        created_signal = sdk.create_signal(signal_data)

        if created_signal:
            return jsonify({
                'success': True,
                'signal': created_signal
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create signal'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
```

## Testing Examples

### Unit Testing

```python
import unittest
from unittest.mock import Mock, patch
import json

from trading_sdk import TradingSignalsSDK

class TestTradingSignalsSDK(unittest.TestCase):

    def setUp(self):
        self.sdk = TradingSignalsSDK(
            base_url="https://test-api.com",
            username="test_user",
            password="test_password"
        )

    @patch('requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh_token'
        }
        mock_post.return_value = mock_response

        result = self.sdk.authenticate()

        self.assertTrue(result)
        self.assertEqual(self.sdk.access_token, 'test_token')
        self.assertEqual(self.sdk.refresh_token, 'test_refresh_token')

    @patch('requests.get')
    def test_get_latest_signals_success(self, mock_get):
        """Test successful get latest signals"""
        self.sdk.access_token = 'test_token'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 1,
                'symbol': 'EURUSD',
                'signal_type': 'BUY',
                'entry_price': 1.0850,
                'reliability': 85.5
            }
        ]
        mock_get.return_value = mock_response

        signals = self.sdk.get_latest_signals()

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]['symbol'], 'EURUSD')

    @patch('requests.post')
    def test_create_signal_success(self, mock_post):
        """Test successful signal creation"""
        self.sdk.access_token = 'test_token'

        signal_data = {
            'symbol': 'EURUSD',
            'signal_type': 'BUY',
            'entry_price': 1.0850,
            'reliability': 85.5
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'signal': {
                'id': 1,
                'symbol': 'EURUSD',
                'signal_type': 'BUY',
                'entry_price': 1.0850,
                'reliability': 85.5
            },
            'success': True
        }
        mock_post.return_value = mock_response

        result = self.sdk.create_signal(signal_data)

        self.assertIsNotNone(result)
        self.assertEqual(result['signal']['symbol'], 'EURUSD')

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```python
import pytest
import requests
import time

class TestTradingAPI:

    @pytest.fixture
    def api_client(self):
        """Test API client fixture"""
        return requests.Session()

    @pytest.fixture
    def auth_token(self, api_client):
        """Get authentication token for testing"""
        response = api_client.post(
            "https://your-api-domain.com/token",
            data={
                "username": "test_user",
                "password": "test_password"
            }
        )

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            pytest.skip("Authentication failed")

    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("https://your-api-domain.com/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_get_signals_unauthorized(self, api_client):
        """Test getting signals without authentication"""
        response = api_client.get("https://your-api-domain.com/api/signals/latest")

        assert response.status_code == 401

    def test_get_signals_authorized(self, api_client, auth_token):
        """Test getting signals with authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = api_client.get(
            "https://your-api-domain.com/api/signals/latest",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_signal(self, api_client, auth_token):
        """Test creating a signal"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        signal_data = {
            "symbol": "EURUSD",
            "signal_type": "BUY",
            "entry_price": 1.0850,
            "reliability": 85.5
        }

        response = api_client.post(
            "https://your-api-domain.com/signals/",
            headers=headers,
            json=signal_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "signal" in data

if __name__ == "__main__":
    pytest.main([__file__])
```

This comprehensive SDK documentation provides examples for various use cases, languages, and integration scenarios. The examples cover basic usage, advanced trading bots, web frameworks, and testing, making it easy for developers to integrate with the AI Trading System API.