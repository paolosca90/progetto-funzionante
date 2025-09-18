# Quick Start Guide: AI Trading System API

This guide will help you get started with the AI Trading System API quickly and efficiently.

## Prerequisites

Before you begin, ensure you have:

- A valid account with API access
- Basic knowledge of REST APIs
- OANDA account (for trading functionality)
- Python 3.8+ or Node.js 16+ (for SDK examples)

## Step 1: Get Your API Credentials

1. **Sign Up**: Register at [https://your-api-domain.com/register](https://your-api-domain.com/register)
2. **Verify Email**: Check your email for verification link
3. **Get Credentials**: Log in and find your API credentials in the dashboard

## Step 2: Set Up Authentication

### Method 1: Using cURL

```bash
# Get your access token
curl -X POST "https://your-api-domain.com/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Response will contain:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Method 2: Using Python

```python
import requests

# Get access token
response = requests.post(
    "https://your-api-domain.com/token",
    data={"username": "your_username", "password": "your_password"}
)

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data["access_token"]
    print("Authentication successful!")
else:
    print("Authentication failed:", response.text)
```

### Method 3: Using JavaScript

```javascript
// Get access token
const response = await fetch('https://your-api-domain.com/token', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: 'username=your_username&password=your_password'
});

if (response.ok) {
    const tokenData = await response.json();
    const accessToken = tokenData.access_token;
    console.log('Authentication successful!');
} else {
    console.error('Authentication failed:', await response.text());
}
```

## Step 3: Make Your First API Call

Once you have your access token, you can start making API calls:

### Get Latest Signals

```bash
curl -X GET "https://your-api-domain.com/api/signals/latest?limit=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Python Example

```python
import requests

def get_latest_signals(access_token, limit=5):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"https://your-api-domain.com/api/signals/latest?limit={limit}",
        headers=headers
    )

    if response.status_code == 200:
        signals = response.json()
        print(f"Retrieved {len(signals)} signals:")
        for signal in signals:
            print(f"- {signal['symbol']}: {signal['signal_type']} @ {signal['entry_price']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Usage
get_latest_signals(access_token)
```

### JavaScript Example

```javascript
async function getLatestSignals(accessToken, limit = 5) {
    const headers = {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    };

    const response = await fetch(
        `https://your-api-domain.com/api/signals/latest?limit=${limit}`,
        { headers }
    );

    if (response.ok) {
        const signals = await response.json();
        console.log(`Retrieved ${signals.length} signals:`);
        signals.forEach(signal => {
            console.log(`- ${signal.symbol}: ${signal.signal_type} @ ${signal.entry_price}`);
        });
    } else {
        console.error(`Error: ${response.status} - ${await response.text()}`);
    }
}

// Usage
getLatestSignals(accessToken);
```

## Step 4: Connect Your OANDA Account

To enable trading functionality, connect your OANDA account:

```bash
curl -X POST "https://your-api-domain.com/api/oanda/connect" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "account_id=123-456-789012-001&environment=demo"
```

## Step 5: Create Your First Signal

### Create a Signal Programmatically

```python
import requests

def create_signal(access_token, signal_data):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://your-api-domain.com/signals/",
        headers=headers,
        json=signal_data
    )

    if response.status_code == 201:
        signal = response.json()
        print("Signal created successfully!")
        return signal
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Example signal data
signal_data = {
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0800,
    "take_profit": 1.0950,
    "reliability": 85.5,
    "ai_analysis": "Technical analysis shows bullish momentum",
    "confidence_score": 87.2,
    "risk_level": "MEDIUM"
}

# Create signal
created_signal = create_signal(access_token, signal_data)
```

## Step 6: Get Market Data

```python
def get_market_data(access_token, symbol):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"https://your-api-domain.com/api/oanda/market-data/{symbol}",
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Get EURUSD market data
market_data = get_market_data(access_token, "EURUSD")
if market_data:
    print(f"EURUSD - Bid: {market_data['bid']}, Ask: {market_data['ask']}")
```

## Step 7: Monitor System Health

```python
def check_system_health(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        "https://your-api-domain.com/health/detailed",
        headers=headers
    )

    if response.status_code == 200:
        health = response.json()
        print(f"System Status: {health['status']}")
        print(f"Components: {len(health['components'])} checked")
        for component, status in health['components'].items():
            print(f"  {component}: {status['status']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Check system health
check_system_health(access_token)
```

## Complete Example: Signal Trading Bot

Here's a complete example of a simple signal trading bot:

```python
import requests
import time
import json

class TradingBot:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None

    def authenticate(self):
        """Authenticate and get tokens"""
        response = requests.post(
            f"{self.base_url}/token",
            data={"username": self.username, "password": self.password}
        )

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            print("✓ Authentication successful")
            return True
        else:
            print("✗ Authentication failed")
            return False

    def get_headers(self):
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_latest_signals(self, limit=10):
        """Get latest signals"""
        response = requests.get(
            f"{self.base_url}/api/signals/latest?limit={limit}",
            headers=self.get_headers()
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Failed to get signals: {response.status_code}")
            return []

    def get_market_data(self, symbol):
        """Get market data for a symbol"""
        response = requests.get(
            f"{self.base_url}/api/oanda/market-data/{symbol}",
            headers=self.get_headers()
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Failed to get market data: {response.status_code}")
            return None

    def calculate_position_size(self, symbol, account_balance, risk_percentage, stop_loss_pips):
        """Calculate position size"""
        data = {
            "symbol": symbol,
            "account_balance": account_balance,
            "risk_percentage": risk_percentage,
            "stop_loss_pips": stop_loss_pips
        }

        response = requests.post(
            f"{self.base_url}/api/calculate-position-size",
            headers=self.get_headers(),
            data=data
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Failed to calculate position size: {response.status_code}")
            return None

    def process_signals(self):
        """Process latest signals"""
        print("📊 Processing signals...")

        signals = self.get_latest_signals(limit=5)
        if not signals:
            return

        for signal in signals:
            print(f"\n📈 Signal: {signal['symbol']} {signal['signal_type']}")
            print(f"   Entry: {signal['entry_price']}")
            print(f"   Stop Loss: {signal['stop_loss']}")
            print(f"   Take Profit: {signal['take_profit']}")
            print(f"   Reliability: {signal['reliability']}%")
            print(f"   Risk Level: {signal['risk_level']}")

            # Get current market data
            market_data = self.get_market_data(signal['symbol'])
            if market_data:
                print(f"   Current Price: {market_data['bid']}/{market_data['ask']}")

                # Calculate position size (example)
                position_calc = self.calculate_position_size(
                    signal['symbol'],
                    account_balance=10000,
                    risk_percentage=0.02,
                    stop_loss_pips=20
                )

                if position_calc:
                    print(f"   Recommended Size: {position_calc['position_size']}")
                    print(f"   Risk Amount: ${position_calc['risk_amount']}")

    def monitor(self, interval=300):
        """Monitor signals at regular intervals"""
        print(f"🚀 Starting trading bot...")
        print(f"⏰ Monitoring every {interval} seconds...")

        try:
            while True:
                self.process_signals()
                print(f"\n💤 Waiting {interval} seconds...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n👋 Trading bot stopped by user")

# Usage
if __name__ == "__main__":
    # Initialize bot
    bot = TradingBot(
        base_url="https://your-api-domain.com",
        username="your_username",
        password="your_password"
    )

    # Authenticate
    if bot.authenticate():
        # Start monitoring
        bot.monitor(interval=300)  # Check every 5 minutes
```

## Common Use Cases

### 1. Signal Analysis Dashboard

```python
def create_signal_dashboard(access_token):
    """Create a simple signal analysis dashboard"""
    import matplotlib.pyplot as plt
    from datetime import datetime, timedelta

    # Get recent signals
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "https://your-api-domain.com/signals/?limit=100",
        headers=headers
    )

    if response.status_code == 200:
        signals = response.json()

        # Analyze signals
        symbols = {}
        for signal in signals:
            symbol = signal['symbol']
            if symbol not in symbols:
                symbols[symbol] = []
            symbols[symbol].append(signal['reliability'])

        # Create visualization
        plt.figure(figsize=(12, 6))

        for symbol, reliabilities in symbols.items():
            if len(reliabilities) > 1:
                plt.plot(reliabilities, label=symbol, marker='o')

        plt.title('Signal Reliability by Symbol')
        plt.xlabel('Signal Number')
        plt.ylabel('Reliability Score')
        plt.legend()
        plt.grid(True)
        plt.show()
```

### 2. Automated Alert System

```python
def setup_signal_alerts(access_token, webhook_url=None):
    """Set up alerts for high-reliability signals"""
    import smtplib
    from email.mime.text import MIMEText

    def check_for_high_reliability_signals():
        response = requests.get(
            "https://your-api-domain.com/signals/latest?limit=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code == 200:
            signals = response.json()
            high_reliability_signals = [
                s for s in signals if s['reliability'] >= 85
            ]

            if high_reliability_signals:
                alert_message = f"High reliability alerts:\n\n"
                for signal in high_reliability_signals:
                    alert_message += f"{signal['symbol']} {signal['signal_type']} - {signal['reliability']}%\n"

                # Send email alert
                send_email_alert(alert_message)

                # Send webhook if provided
                if webhook_url:
                    send_webhook_alert(webhook_url, high_reliability_signals)

    def send_email_alert(message):
        """Send email alert"""
        # Configure your email settings
        sender = "your_email@example.com"
        receiver = "your_email@example.com"

        msg = MIMEText(message)
        msg['Subject'] = 'High Reliability Signal Alert'
        msg['From'] = sender
        msg['To'] = receiver

        # Send email (configure your SMTP settings)
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender, "your_password")
                server.send_message(msg)
            print("✓ Email alert sent")
        except Exception as e:
            print(f"✗ Failed to send email: {e}")

    def send_webhook_alert(url, signals):
        """Send webhook alert"""
        try:
            response = requests.post(
                url,
                json={
                    "event": "high_reliability_signals",
                    "signals": signals,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            if response.status_code == 200:
                print("✓ Webhook alert sent")
            else:
                print(f"✗ Webhook failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Webhook error: {e}")

    return check_for_high_reliability_signals

# Usage
alert_checker = setup_signal_alerts(access_token)
alert_checker()  # Check immediately
```

## Next Steps

1. **Explore the API**: Check the full [API Documentation](API_DOCUMENTATION.md)
2. **Use the SDK**: Download the official SDK for your preferred language
3. **Join the Community**: Connect with other developers in our community forum
4. **Monitor Performance**: Set up monitoring and alerts for your applications
5. **Scale Your Application**: Learn about rate limiting and optimization

## Getting Help

- **Documentation**: [Full API Documentation](API_DOCUMENTATION.md)
- **Examples**: [SDK Examples](SDK_EXAMPLES.md)
- **Support**: support@trading-system.com
- **Community**: https://community.trading-system.com

## Troubleshooting

If you encounter issues:

1. **Check Authentication**: Ensure your token is valid
2. **Rate Limits**: Monitor your API usage
3. **System Status**: Check the health endpoints
4. **Error Messages**: Read error responses carefully
5. **Logs**: Check application logs for detailed errors

For more detailed troubleshooting, see the [Troubleshooting Guide](TROUBLESHOOTING.md).