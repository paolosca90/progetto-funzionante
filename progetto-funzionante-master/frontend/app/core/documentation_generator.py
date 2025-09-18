"""
Interactive Documentation Generator and OpenAPI Tools

This module provides comprehensive documentation generation including:
- Interactive API documentation website
- SDK generation templates
- OpenAPI specification export
- Example code generation
- Client library documentation
- Testing utilities
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

class DocumentationGenerator:
    """Generate comprehensive API documentation and SDKs"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.openapi_spec = self.app.openapi()
        self.output_dir = Path("docs")
        self.output_dir.mkdir(exist_ok=True)

    def generate_all_documentation(self) -> Dict[str, str]:
        """
        Generate all documentation artifacts

        Returns:
            Dict[str, str]: Generated file paths and their descriptions
        """
        generated_files = {}

        # Generate OpenAPI specifications
        generated_files["openapi_json"] = self.generate_openapi_json()
        generated_files["openapi_yaml"] = self.generate_openapi_yaml()

        # Generate documentation website
        generated_files["html_docs"] = self.generate_html_documentation()
        generated_files["markdown_docs"] = self.generate_markdown_documentation()

        # Generate SDK templates
        generated_files["python_sdk"] = self.generate_python_sdk()
        generated_files["javascript_sdk"] = self.generate_javascript_sdk()
        generated_files["curl_examples"] = self.generate_curl_examples()

        # Generate testing tools
        generated_files["postman_collection"] = self.generate_postman_collection()
        generated_files["insomnia_collection"] = self.generate_insomnia_collection()

        # Generate client documentation
        generated_files["client_guide"] = self.generate_client_guide()
        generated_files["quick_start"] = self.generate_quick_start_guide()

        return generated_files

    def generate_openapi_json(self) -> str:
        """Generate OpenAPI specification in JSON format"""
        output_file = self.output_dir / "openapi.json"

        # Enhance OpenAPI spec with additional metadata
        enhanced_spec = self.openapi_spec.copy()
        enhanced_spec["info"]["x-generated-at"] = datetime.utcnow().isoformat()
        enhanced_spec["info"]["x-generator"] = "AI Cash Revolution API Documentation Generator"
        enhanced_spec["info"]["x-version"] = "1.0.0"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enhanced_spec, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated OpenAPI JSON specification: {output_file}")
        return str(output_file)

    def generate_openapi_yaml(self) -> str:
        """Generate OpenAPI specification in YAML format"""
        output_file = self.output_dir / "openapi.yaml"

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(self.openapi_spec, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Generated OpenAPI YAML specification: {output_file}")
        return str(output_file)

    def generate_html_documentation(self) -> str:
        """Generate interactive HTML documentation website"""
        output_file = self.output_dir / "index.html"

        html_content = self._generate_html_template()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Generated HTML documentation: {output_file}")
        return str(output_file)

    def generate_markdown_documentation(self) -> str:
        """Generate comprehensive Markdown documentation"""
        output_file = self.output_dir / "API_DOCUMENTATION.md"

        markdown_content = self._generate_markdown_content()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Generated Markdown documentation: {output_file}")
        return str(output_file)

    def generate_python_sdk(self) -> str:
        """Generate Python SDK template"""
        sdk_dir = self.output_dir / "python_sdk"
        sdk_dir.mkdir(exist_ok=True)

        # Main SDK file
        main_sdk = sdk_dir / "__init__.py"
        main_sdk_content = self._generate_python_sdk_main()

        with open(main_sdk, "w", encoding="utf-8") as f:
            f.write(main_sdk_content)

        # Models file
        models_file = sdk_dir / "models.py"
        models_content = self._generate_python_sdk_models()

        with open(models_file, "w", encoding="utf-8") as f:
            f.write(models_content)

        # Requirements file
        requirements_file = sdk_dir / "requirements.txt"
        requirements_content = self._generate_python_sdk_requirements()

        with open(requirements_file, "w", encoding="utf-8") as f:
            f.write(requirements_content)

        logger.info(f"Generated Python SDK: {sdk_dir}")
        return str(sdk_dir)

    def generate_javascript_sdk(self) -> str:
        """Generate JavaScript SDK template"""
        sdk_dir = self.output_dir / "javascript_sdk"
        sdk_dir.mkdir(exist_ok=True)

        # Main SDK file
        main_sdk = sdk_dir / "index.js"
        main_sdk_content = self._generate_javascript_sdk_main()

        with open(main_sdk, "w", encoding="utf-8") as f:
            f.write(main_sdk_content)

        # Package.json
        package_file = sdk_dir / "package.json"
        package_content = self._generate_javascript_package_json()

        with open(package_file, "w", encoding="utf-8") as f:
            f.write(package_content)

        logger.info(f"Generated JavaScript SDK: {sdk_dir}")
        return str(sdk_dir)

    def generate_curl_examples(self) -> str:
        """Generate cURL examples for all endpoints"""
        output_file = self.output_dir / "curl_examples.md"

        examples = self._generate_curl_examples_content()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(examples)

        logger.info(f"Generated cURL examples: {output_file}")
        return str(output_file)

    def generate_postman_collection(self) -> str:
        """Generate Postman collection"""
        output_file = self.output_dir / "postman_collection.json"

        collection = self._generate_postman_collection_content()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2)

        logger.info(f"Generated Postman collection: {output_file}")
        return str(output_file)

    def generate_insomnia_collection(self) -> str:
        """Generate Insomnia collection"""
        output_file = self.output_dir / "insomnia_collection.json"

        collection = self._generate_insomnia_collection_content()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2)

        logger.info(f"Generated Insomnia collection: {output_file}")
        return str(output_file)

    def generate_client_guide(self) -> str:
        """Generate comprehensive client integration guide"""
        output_file = self.output_dir / "CLIENT_INTEGRATION_GUIDE.md"

        guide_content = self._generate_client_guide_content()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(guide_content)

        logger.info(f"Generated client integration guide: {output_file}")
        return str(output_file)

    def generate_quick_start_guide(self) -> str:
        """Generate quick start guide"""
        output_file = self.output_dir / "QUICK_START.md"

        quick_start = self._generate_quick_start_content()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(quick_start)

        logger.info(f"Generated quick start guide: {output_file}")
        return str(output_file)

    def _generate_html_template(self) -> str:
        """Generate interactive HTML documentation template"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Cash Revolution API Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }}
        .header p {{
            margin: 1rem 0 0 0;
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        .api-info {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 2rem 0;
            flex-wrap: wrap;
        }}
        .info-card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            flex: 1;
            min-width: 250px;
            text-align: center;
        }}
        .info-card h3 {{
            margin: 0 0 1rem 0;
            color: #333;
        }}
        .info-card p {{
            margin: 0;
            color: #666;
            font-size: 0.9rem;
        }}
        .info-card .number {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Cash Revolution Trading API</h1>
        <p>Professional AI-powered trading signals platform with comprehensive documentation</p>
    </div>

    <div class="api-info">
        <div class="info-card">
            <div class="number">2.0.1</div>
            <h3>API Version</h3>
            <p>Latest stable release with enhanced features</p>
        </div>
        <div class="info-card">
            <div class="number">50+</div>
            <h3>Endpoints</h3>
            <p>Comprehensive trading and management APIs</p>
        </div>
        <div class="info-card">
            <div class="number">24/7</div>
            <h3>Availability</h3>
            <p>Continuous service with real-time data</p>
        </div>
        <div class="info-card">
            <div class="number">99.9%</div>
            <h3>Uptime</h3>
            <p>Highly reliable trading infrastructure</p>
        </div>
    </div>

    <div id="redoc-container"></div>

    <script>
        // Initialize ReDoc with custom configuration
        Redoc.init(
            {json.decode(json.dumps({self.openapi_spec}))},
            {{
                theme: {{
                    colors: {{
                        primary: {{
                            main: '#667eea'
                        }},
                        success: {{
                            main: '#48bb78'
                        }},
                        warning: {{
                            main: '#f6ad55'
                        }},
                        danger: {{
                            main: '#f56565'
                        }}
                    }},
                    typography: {{
                        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        fontSize: '16px',
                        lineHeight: '1.5'
                    }},
                    sidebar: {{
                        backgroundColor: '#f7fafc',
                        textColor: '#2d3748'
                    }},
                    rightPanel: {{
                        backgroundColor: '#ffffff'
                    }}
                }},
                hideHostname: false,
                expandSingleSchemaField: true,
                pathInMiddlePanel: true,
                jsonSampleExpandLevel: 2,
                requiredPropsFirst: true,
                sortPropsAlphabetically: false,
                showExtensions: true,
                showWebhookVerb: true,
                nativeScrollbars: false,
                scrollYOffset: 50,
                menuToggle: true,
                suppressWarnings: false,
                expandResponses: 'all',
                generateCodeSamples: {{
                    languages: [
                        {{
                            lang: 'curl',
                            label: 'cURL',
                            source: `
// Install dependencies
npm install cash-revolution-sdk

// Import SDK
const {{ CashRevolutionAPI }} = require('cash-revolution-sdk');

// Initialize API client
const api = new CashRevolutionAPI({{
  apiKey: 'your_api_key_here',
  baseUrl: 'https://api.cash-revolution.com/v2'
}});

// Get latest signals
const signals = await api.signals.getLatest({{
  limit: 10,
  minReliability: 80
}});

console.log('Latest signals:', signals);
                            `
                        }},
                        {{
                            lang: 'python',
                            label: 'Python',
                            source: `
# Install dependencies
pip install cash-revolution-sdk

# Import SDK
from cash_revolution import CashRevolutionAPI

# Initialize API client
api = CashRevolutionAPI(
    api_key='your_api_key_here',
    base_url='https://api.cash-revolution.com/v2'
)

# Get latest signals
signals = api.signals.get_latest(
    limit=10,
    min_reliability=80
)

print('Latest signals:', signals)
                            `
                        }},
                        {{
                            lang: 'javascript',
                            label: 'JavaScript (Fetch)',
                            source: `
// Get authentication token
const loginResponse = await fetch('https://api.cash-revolution.com/auth/token', {{
  method: 'POST',
  headers: {{
    'Content-Type': 'application/x-www-form-urlencoded',
  }},
  body: 'username=your_username&password=your_password'
}});

const {{ access_token }} = await loginResponse.json();

// Get latest signals
const signalsResponse = await fetch('https://api.cash-revolution.com/signals/latest?limit=10&min_reliability=80', {{
  headers: {{
    'Authorization': \`Bearer \${{access_token}}\`,
    'Content-Type': 'application/json'
  }}
}});

const signals = await signalsResponse.json();
console.log('Latest signals:', signals);
                            `
                        }}
                    ]
                }}
            }},
            document.getElementById('redoc-container')
        );
    </script>
</body>
</html>
        """

    def _generate_markdown_content(self) -> str:
        """Generate comprehensive Markdown documentation"""
        api_info = self.openapi_spec.get("info", {})
        servers = self.openapi_spec.get("servers", [])
        paths = self.openapi_spec.get("paths", {})

        content = f"""# AI Cash Revolution Trading API Documentation

## Overview

{api_info.get("description", "Professional AI-powered trading signals platform with OANDA integration")}

**Version:** {api_info.get("version", "2.0.1")}
**Contact:** {api_info.get("contact", {}).get("email", "support@cash-revolution.com")}
**License:** {api_info.get("license", {}).get("name", "MIT License")}

## Quick Start

### 1. Authentication

```bash
# Get JWT token
curl -X POST "https://api.cash-revolution.com/auth/token" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=your_username&password=your_password"
```

### 2. Get Latest Signals

```bash
# Get latest signals with filtering
curl -X GET "https://api.cash-revolution.com/signals/latest?limit=10&min_reliability=80" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Create Signal

```bash
# Create a new trading signal
curl -X POST "https://api.cash-revolution.com/signals/" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "symbol": "EUR_USD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0820,
    "take_profit": 1.0900,
    "reliability": 85.5,
    "confidence_score": 87.0,
    "risk_level": "MEDIUM"
  }}'
```

## Server Information

"""

        for server in servers:
            content += f"- **{server.get('description', 'Server')}**: {server.get('url', 'N/A')}\n"

        content += "\n## Authentication\n\n"
        content += """The API uses JWT Bearer tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer your_jwt_token_here
```

### Rate Limits

- **Authentication endpoints**: 5 requests per minute
- **API endpoints**: 100 requests per minute
- **Signal generation**: 10 requests per hour
- **Market data**: 60 requests per minute

## API Endpoints

"""

        for path, methods in paths.items():
            content += f"### {path}\n\n"

            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    operation_id = details.get("operationId", f"{method.upper()} {path}")
                    summary = details.get("summary", "No description available")

                    content += f"#### {method.upper()} {path}\n"
                    content += f"**Operation ID**: `{operation_id}`\n\n"
                    content += f"**Summary**: {summary}\n\n"

                    if "parameters" in details:
                        content += "**Parameters**:\n"
                        for param in details["parameters"]:
                            param_name = param.get("name", "Unknown")
                            param_type = param.get("schema", {}).get("type", "string")
                            required = "Required" if param.get("required", False) else "Optional"
                            description = param.get("description", "No description")

                            content += f"- `{param_name}` ({param_type}, {required}): {description}\n"
                        content += "\n"

                    if "requestBody" in details:
                        content += "**Request Body**:\n"
                        content += "```json\n"
                        content += json.dumps(details["requestBody"].get("content", {}).get("application/json", {}).get("example", {}), indent=2)
                        content += "\n```\n\n"

                    if "responses" in details:
                        content += "**Responses**:\n"
                        for status_code, response in details["responses"].items():
                            description = response.get("description", "No description")
                            content += f"- **{status_code}**: {description}\n"
                        content += "\n"

        content += "## Error Handling\n\n"
        content += """The API uses standard HTTP status codes and returns error information in a consistent format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "status_code": 400,
  "category": "ValidationError",
  "severity": "low",
  "details": {},
  "field_errors": [],
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "help_url": "https://docs.cash-revolution.com/errors/validation"
}
```

## SDKs and Libraries

### Python SDK

```python
# Install
pip install cash-revolution-sdk

# Usage
from cash_revolution import CashRevolutionAPI

api = CashRevolutionAPI(api_key='your_api_key')
signals = api.signals.get_latest(limit=10)
```

### JavaScript SDK

```javascript
// Install
npm install cash-revolution-sdk

// Usage
const {{ CashRevolutionAPI }} = require('cash-revolution-sdk');
const api = new CashRevolutionAPI(api_key='your_api_key');
const signals = await api.signals.getLatest({{ limit: 10 }});
```

## Support

- **Documentation**: https://docs.cash-revolution.com
- **API Status**: https://status.cash-revolution.com
- **Support Email**: support@cash-revolution.com
- **Issues**: https://github.com/cash-revolution/api/issues

---
*Generated on {datetime.utcnow().isoformat()}*
"""

        return content

    def _generate_python_sdk_main(self) -> str:
        """Generate Python SDK main file"""
        return '''"""
AI Cash Revolution Python SDK

This SDK provides convenient access to the AI Cash Revolution Trading API.
"""

import requests
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from .models import Signal, User, MarketData

class CashRevolutionAPI:
    """Main API client for AI Cash Revolution Trading API"""

    def __init__(self, api_key: str, base_url: str = "https://api.cash-revolution.com/v2"):
        """
        Initialize the API client

        Args:
            api_key: Your API key or JWT token
            base_url: Base URL for the API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'cash-revolution-python-sdk/1.0.0'
        })

    class Signals:
        """Signals API endpoints"""

        def __init__(self, client):
            self.client = client

        def get_latest(self, limit: int = 10, min_reliability: float = None,
                      risk_level: str = None, symbol: str = None) -> List[Signal]:
            """
            Get latest trading signals

            Args:
                limit: Maximum number of signals to return
                min_reliability: Minimum reliability score filter
                risk_level: Risk level filter (LOW, MEDIUM, HIGH)
                symbol: Filter by specific symbol

            Returns:
                List[Signal]: List of trading signals
            """
            params = {'limit': limit}
            if min_reliability is not None:
                params['min_reliability'] = min_reliability
            if risk_level:
                params['risk_level'] = risk_level
            if symbol:
                params['symbol'] = symbol

            response = self.client.session.get(f'{self.client.base_url}/signals/latest', params=params)
            response.raise_for_status()

            return [Signal.from_dict(signal_data) for signal_data in response.json()]

        def create(self, signal_data: Dict[str, Any]) -> Signal:
            """
            Create a new trading signal

            Args:
                signal_data: Signal creation data

            Returns:
                Signal: Created signal
            """
            response = self.client.session.post(f'{self.client.base_url}/signals/', json=signal_data)
            response.raise_for_status()

            return Signal.from_dict(response.json())

        def get_market_data(self, symbol: str) -> MarketData:
            """
            Get real-time market data for a symbol

            Args:
                symbol: Trading symbol (e.g., EUR_USD)

            Returns:
                MarketData: Real-time market data
            """
            response = self.client.session.get(f'{self.client.base_url}/signals/market-data/{symbol}')
            response.raise_for_status()

            return MarketData.from_dict(response.json())

    class Auth:
        """Authentication API endpoints"""

        def __init__(self, client):
            self.client = client

        def login(self, username: str, password: str) -> Dict[str, str]:
            """
            Login and get JWT tokens

            Args:
                username: Username or email
                password: Password

            Returns:
                Dict[str, str]: Access and refresh tokens
            """
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {'username': username, 'password': password}

            response = self.client.session.post(f'{self.client.base_url}/auth/token',
                                             headers=headers, data=data)
            response.raise_for_status()

            return response.json()

        def register(self, user_data: Dict[str, Any]) -> User:
            """
            Register a new user

            Args:
                user_data: User registration data

            Returns:
                User: Created user
            """
            response = self.client.session.post(f'{self.client.base_url}/auth/register',
                                             json=user_data)
            response.raise_for_status()

            return User.from_dict(response.json())

    def __init__(self, api_key: str, base_url: str = "https://api.cash-revolution.com/v2"):
        """Initialize API client with authentication and endpoints"""
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'cash-revolution-python-sdk/1.0.0'
        })

        # Initialize API endpoints
        self.signals = self.Signals(self)
        self.auth = self.Auth(self)

    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status

        Returns:
            Dict[str, Any]: Health status information
        """
        response = self.session.get(f'{self.base_url}/health')
        response.raise_for_status()

        return response.json()

# Example usage
if __name__ == "__main__":
    # Initialize API client
    api = CashRevolutionAPI(api_key='your_api_key_here')

    # Get latest signals
    try:
        signals = api.signals.get_latest(limit=5)
        print(f"Retrieved {len(signals)} signals")

        for signal in signals:
            print(f"Signal: {signal.symbol} - {signal.signal_type}")
            print(f"Entry Price: {signal.entry_price}")
            print(f"Reliability: {signal.reliability}%")
            print("---")

    except Exception as e:
        print(f"Error: {e}")
'''

    def _generate_python_sdk_models(self) -> str:
        """Generate Python SDK models"""
        return '''"""
Data models for the AI Cash Revolution API
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Signal:
    """Trading signal model"""
    id: int
    symbol: str
    signal_type: str
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reliability: float = 0.0
    confidence_score: float = 0.0
    risk_level: str = "MEDIUM"
    status: str = "ACTIVE"
    timeframe: str = "H1"
    ai_analysis: Optional[str] = None
    expires_at: Optional[datetime] = None
    market_session: str = "LONDON"
    volatility: float = 0.0
    spread: float = 0.0
    risk_reward_ratio: float = 0.0
    position_size_suggestion: float = 0.01
    technical_score: float = 0.0
    rsi: Optional[float] = None
    macd_signal: Optional[float] = None
    is_public: bool = True
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    source: str = "OANDA_AI"
    creator_id: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """Create Signal from dictionary"""
        # Handle datetime conversion
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if 'expires_at' in data and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))

        return cls(**data)

@dataclass
class User:
    """User model"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    subscription_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    email_verified: bool = False
    profile_complete: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary"""
        # Handle datetime conversion
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if 'last_login' in data and data['last_login']:
            data['last_login'] = datetime.fromisoformat(data['last_login'].replace('Z', '+00:00'))
        if 'trial_end' in data and data['trial_end']:
            data['trial_end'] = datetime.fromisoformat(data['trial_end'].replace('Z', '+00:00'))

        return cls(**data)

@dataclass
class MarketData:
    """Market data model"""
    symbol: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    session: str = "LONDON"
    volatility: float = 0.0
    volume_24h: Optional[float] = None
    daily_change: Optional[float] = None
    technical_indicators: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        """Create MarketData from dictionary"""
        # Handle datetime conversion
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

        return cls(**data)

@dataclass
class ErrorResponse:
    """Error response model"""
    error: str
    message: str
    status_code: int
    category: str
    severity: str
    details: Dict[str, Any] = field(default_factory=dict)
    field_errors: List[Dict[str, Any]] = field(default_factory=list)
    request_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    help_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorResponse':
        """Create ErrorResponse from dictionary"""
        # Handle datetime conversion
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

        return cls(**data)
'''

    def _generate_python_sdk_requirements(self) -> str:
        """Generate Python SDK requirements"""
        return '''requests>=2.28.0
dataclasses-json>=0.5.7
python-dateutil>=2.8.2
'''

    def _generate_javascript_sdk_main(self) -> str:
        """Generate JavaScript SDK main file"""
        return '''/**
 * AI Cash Revolution JavaScript SDK
 *
 * This SDK provides convenient access to the AI Cash Revolution Trading API.
 */

class CashRevolutionAPI {
    constructor(options = {}) {
        this.apiKey = options.apiKey || '';
        this.baseUrl = options.baseUrl || 'https://api.cash-revolution.com/v2';
        this.timeout = options.timeout || 30000;
    }

    /**
     * Make HTTP request to API
     */
    async _request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method: options.method || 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
                'User-Agent': 'cash-revolution-javascript-sdk/1.0.0',
                ...options.headers
            },
            timeout: this.timeout,
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    /**
     * Authentication endpoints
     */
    auth = {
        /**
         * Login and get JWT tokens
         */
        login: async (username, password) => {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            return await this._request('/auth/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });
        },

        /**
         * Register new user
         */
        register: async (userData) => {
            return await this._request('/auth/register', {
                method: 'POST',
                body: userData
            });
        },

        /**
         * Request password reset
         */
        forgotPassword: async (email) => {
            const formData = new URLSearchParams();
            formData.append('email', email);

            return await this._request('/auth/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });
        }
    };

    /**
     * Signals endpoints
     */
    signals = {
        /**
         * Get latest trading signals
         */
        getLatest: async (options = {}) => {
            const params = new URLSearchParams();

            if (options.limit) params.append('limit', options.limit);
            if (options.minReliability) params.append('min_reliability', options.minReliability);
            if (options.riskLevel) params.append('risk_level', options.riskLevel);
            if (options.signalType) params.append('signal_type', options.signalType);
            if (options.timeframe) params.append('timeframe', options.timeframe);
            if (options.symbol) params.append('symbol', options.symbol);

            const queryString = params.toString();
            const endpoint = `/signals/latest${queryString ? `?${queryString}` : ''}`;

            return await this._request(endpoint);
        },

        /**
         * Create new trading signal
         */
        create: async (signalData) => {
            return await this._request('/signals/', {
                method: 'POST',
                body: signalData
            });
        },

        /**
         * Get market data for symbol
         */
        getMarketData: async (symbol) => {
            return await this._request(`/signals/market-data/${symbol}`);
        },

        /**
         * Search signals
         */
        search: async (query, options = {}) => {
            const params = new URLSearchParams();
            params.append('q', query);

            if (options.minReliability) params.append('min_reliability', options.minReliability);
            if (options.maxAgeHours) params.append('max_age_hours', options.maxAgeHours);
            if (options.signalType) params.append('signal_type', options.signalType);
            if (options.riskLevel) params.append('risk_level', options.riskLevel);
            if (options.page) params.append('page', options.page);
            if (options.perPage) params.append('per_page', options.perPage);

            const queryString = params.toString();
            const endpoint = `/signals/search${queryString ? `?${queryString}` : ''}`;

            return await this._request(endpoint);
        }
    };

    /**
     * Users endpoints
     */
    users = {
        /**
         * Get current user profile
         */
        getProfile: async () => {
            return await this._request('/users/me');
        },

        /**
         * Update user profile
         */
        updateProfile: async (profileData) => {
            return await this._request('/users/profile', {
                method: 'PATCH',
                body: profileData
            });
        }
    };

    /**
     * Health check
     */
    healthCheck: async () => {
        return await this._request('/health');
    }

    /**
     * Set API key
     */
    setApiKey(apiKey) {
        this.apiKey = apiKey;
    }

    /**
     * Set base URL
     */
    setBaseUrl(baseUrl) {
        this.baseUrl = baseUrl;
    }
}

// Export for CommonJS
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CashRevolutionAPI;
}

// Export for ES modules
if (typeof export !== 'undefined') {
    export default CashRevolutionAPI;
}

// Browser global
if (typeof window !== 'undefined') {
    window.CashRevolutionAPI = CashRevolutionAPI;
}

// Example usage
/*
const api = new CashRevolutionAPI({
    apiKey: 'your_api_key_here'
});

// Get latest signals
api.signals.getLatest({ limit: 10, minReliability: 80 })
    .then(signals => {
        console.log('Latest signals:', signals);
    })
    .catch(error => {
        console.error('Error:', error.message);
    });
*/
'''

    def _generate_javascript_package_json(self) -> str:
        """Generate JavaScript package.json"""
        return '''{
  "name": "cash-revolution-sdk",
  "version": "1.0.0",
  "description": "JavaScript SDK for AI Cash Revolution Trading API",
  "main": "index.js",
  "types": "index.d.ts",
  "scripts": {
    "test": "jest",
    "build": "tsc",
    "lint": "eslint src/**/*.js",
    "format": "prettier --write src/**/*.js"
  },
  "keywords": [
    "trading",
    "api",
    "signals",
    "oanda",
    "ai",
    "cash-revolution"
  ],
  "author": "AI Cash Revolution",
  "license": "MIT",
  "dependencies": {
    "node-fetch": "^2.6.7"
  },
  "devDependencies": {
    "@types/node": "^18.0.0",
    "jest": "^29.0.0",
    "eslint": "^8.0.0",
    "prettier": "^2.7.0",
    "typescript": "^4.8.0"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/cash-revolution/javascript-sdk.git"
  },
  "bugs": {
    "url": "https://github.com/cash-revolution/javascript-sdk/issues"
  },
  "homepage": "https://docs.cash-revolution.com",
  "engines": {
    "node": ">=14.0.0"
  }
}'''

    def _generate_curl_examples_content(self) -> str:
        """Generate cURL examples documentation"""
        return """# cURL Examples for AI Cash Revolution API

This document provides comprehensive cURL examples for all API endpoints.

## Authentication

### Login and Get Token

```bash
curl -X POST "https://api.cash-revolution.com/auth/token" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=your_username&password=your_password"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Register New User

```bash
curl -X POST "https://api.cash-revolution.com/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "trader123",
    "email": "trader@example.com",
    "password": "SecurePass123!",
    "full_name": "John Trader"
  }'
```

### Password Reset

```bash
curl -X POST "https://api.cash-revolution.com/auth/forgot-password" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "email=trader@example.com"
```

## Trading Signals

### Get Latest Signals

```bash
# Basic request
curl -X GET "https://api.cash-revolution.com/signals/latest" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# With filtering
curl -X GET "https://api.cash-revolution.com/signals/latest?limit=10&min_reliability=80&risk_level=MEDIUM" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Symbol-specific
curl -X GET "https://api.cash-revolution.com/signals/latest?symbol=EUR_USD&timeframe=H1" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Signal

```bash
curl -X POST "https://api.cash-revolution.com/signals/" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "symbol": "EUR_USD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0820,
    "take_profit": 1.0900,
    "reliability": 85.5,
    "confidence_score": 87.0,
    "risk_level": "MEDIUM",
    "timeframe": "H1",
    "ai_analysis": "Strong bullish momentum detected with RSI oversold bounce",
    "market_session": "LONDON",
    "volatility": 0.0012,
    "spread": 0.0001,
    "risk_reward_ratio": 2.5,
    "position_size_suggestion": 0.01,
    "technical_score": 78.0
  }'
```

### Get Market Data

```bash
curl -X GET "https://api.cash-revolution.com/signals/market-data/EUR_USD" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Search Signals

```bash
curl -X GET "https://api.cash-revolution.com/signals/search?q=EURUSD%20bullish&min_reliability=80&page=1&per_page=20" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## User Management

### Get User Profile

```bash
curl -X GET "https://api.cash-revolution.com/users/me" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Profile

```bash
curl -X PATCH "https://api.cash-revolution.com/users/profile" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "full_name=John%20Trader%20Smith&email=john.smith@example.com"
```

## Health Check

```bash
curl -X GET "https://api.cash-revolution.com/health"
```

## Error Handling

### Handling Rate Limits

```bash
# Check rate limit headers
curl -v -X GET "https://api.cash-revolution.com/signals/latest" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Look for these headers in the response:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 99
# X-RateLimit-Reset: 1642198800
```

### Error Response Example

```bash
# Try to access without authentication
curl -X GET "https://api.cash-revolution.com/signals/latest"

# Response:
{
  "error": "AuthenticationError",
  "message": "Valid authentication token required",
  "status_code": 401,
  "category": "AuthenticationError",
  "severity": "high",
  "details": {},
  "field_errors": [],
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "help_url": "https://docs.cash-revolution.com/errors/authentication"
}
```

## Advanced Usage

### Using API Key Authentication

```bash
# Alternative authentication using API key
curl -X GET "https://api.cash-revolution.com/signals/latest" \\
  -H "X-API-Key: your_api_key_here"
```

### File Upload Example

```bash
# Upload profile image (if supported)
curl -X POST "https://api.cash-revolution.com/users/profile-image" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@profile_image.jpg"
```

### Bulk Operations

```bash
# Create multiple signals (if supported)
curl -X POST "https://api.cash-revolution.com/signals/bulk" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "signals": [
      {
        "symbol": "EUR_USD",
        "signal_type": "BUY",
        "entry_price": 1.0850,
        "reliability": 85.0
      },
      {
        "symbol": "GBPUSD",
        "signal_type": "SELL",
        "entry_price": 1.2650,
        "reliability": 78.0
      }
    ]
  }'
```

## Best Practices

### 1. Store Tokens Securely

```bash
# Store token in environment variable
export TOKEN="your_jwt_token_here"

# Use in cURL commands
curl -H "Authorization: Bearer $TOKEN" "https://api.cash-revolution.com/signals/latest"
```

### 2. Handle Timeouts

```bash
# Set timeout for requests
curl --max-time 30 -X GET "https://api.cash-revolution.com/signals/latest" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Retry Logic

```bash
# Simple retry with exponential backoff
#!/bin/bash

TOKEN="your_token_here"
URL="https://api.cash-revolution.com/signals/latest"
MAX_RETRIES=3
RETRY_DELAY=1

for i in $(seq 1 $MAX_RETRIES); do
    response=$(curl -s -w "%{http_code}" -X GET "$URL" -H "Authorization: Bearer $TOKEN")
    http_code="${response: -3}"
    body="${response%???}"

    if [ "$http_code" = "200" ]; then
        echo "Success: $body"
        break
    elif [ "$http_code" = "429" ]; then
        echo "Rate limited, retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
        RETRY_DELAY=$((RETRY_DELAY * 2))
    else
        echo "Error $http_code: $body"
        break
    fi
done
```

### 4. Log Responses

```bash
# Log request and response
curl -v -X GET "https://api.cash-revolution.com/signals/latest" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" > api_response.log 2>&1
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check your token is valid and not expired
2. **403 Forbidden**: Check your subscription status and permissions
3. **429 Too Many Requests**: Implement rate limiting in your application
4. **500 Internal Server Error**: Check server status and try again later

### Debug Headers

```bash
# Show all headers in response
curl -I -X GET "https://api.cash-revolution.com/signals/latest" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test Connectivity

```bash
# Test basic connectivity
curl -I https://api.cash-revolution.com/health

# Test authentication
curl -I -H "Authorization: Bearer YOUR_TOKEN" https://api.cash-revolution.com/users/me
```

---
*Generated on $(date)*
"""

    def _generate_postman_collection_content(self) -> Dict[str, Any]:
        """Generate Postman collection"""
        return {
            "info": {
                "name": "AI Cash Revolution API",
                "description": "Comprehensive API collection for AI Cash Revolution Trading Platform",
                "version": "2.0.1",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "https://api.cash-revolution.com/v2",
                    "type": "string"
                },
                {
                    "key": "access_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": [
                {
                    "name": "Authentication",
                    "item": [
                        {
                            "name": "Login",
                            "request": {
                                "method": "POST",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/x-www-form-urlencoded"
                                    }
                                ],
                                "body": {
                                    "mode": "urlencoded",
                                    "urlencoded": [
                                        {
                                            "key": "username",
                                            "value": "{{username}}",
                                            "type": "text"
                                        },
                                        {
                                            "key": "password",
                                            "value": "{{password}}",
                                            "type": "text"
                                        }
                                    ]
                                },
                                "url": {
                                    "raw": "{{base_url}}/auth/token",
                                    "host": ["{{base_url}}"],
                                    "path": ["auth", "token"]
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "Signals",
                    "item": [
                        {
                            "name": "Get Latest Signals",
                            "request": {
                                "method": "GET",
                                "header": [],
                                "url": {
                                    "raw": "{{base_url}}/signals/latest?limit=10&min_reliability=80",
                                    "host": ["{{base_url}}"],
                                    "path": ["signals", "latest"],
                                    "query": [
                                        {
                                            "key": "limit",
                                            "value": "10",
                                            "description": "Maximum number of signals to return"
                                        },
                                        {
                                            "key": "min_reliability",
                                            "value": "80",
                                            "description": "Minimum reliability score filter"
                                        }
                                    ]
                                }
                            }
                        },
                        {
                            "name": "Create Signal",
                            "request": {
                                "method": "POST",
                                "header": [],
                                "body": {
                                    "mode": "raw",
                                    "raw": JSON.dumps({
                                        "symbol": "EUR_USD",
                                        "signal_type": "BUY",
                                        "entry_price": 1.0850,
                                        "stop_loss": 1.0820,
                                        "take_profit": 1.0900,
                                        "reliability": 85.5,
                                        "confidence_score": 87.0,
                                        "risk_level": "MEDIUM",
                                        "timeframe": "H1"
                                    }, indent=2)
                                },
                                "url": {
                                    "raw": "{{base_url}}/signals/",
                                    "host": ["{{base_url}}"],
                                    "path": ["signals", ""]
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "Market Data",
                    "item": [
                        {
                            "name": "Get Market Data",
                            "request": {
                                "method": "GET",
                                "header": [],
                                "url": {
                                    "raw": "{{base_url}}/signals/market-data/EUR_USD",
                                    "host": ["{{base_url}}"],
                                    "path": ["signals", "market-data", "EUR_USD"]
                                }
                            }
                        }
                    ]
                }
            ]
        }

    def _generate_insomnia_collection_content(self) -> Dict[str, Any]:
        """Generate Insomnia collection"""
        return {
            "_type": "export",
            "__export_format": 4,
            "__export_date": datetime.utcnow().isoformat(),
            "__export_source": "insomnia.desktop.app:v2022.7.0",
            "resources": [
                {
                    "_id": "req_1",
                    "_type": "request",
                    "url": "{{base_url}}/auth/token",
                    "name": "Login",
                    "method": "POST",
                    "body": {
                        "mimeType": "application/x-www-form-urlencoded",
                        "params": [
                            {
                                "name": "username",
                                "value": "{{username}}"
                            },
                            {
                                "name": "password",
                                "value": "{{password}}"
                            }
                        ]
                    },
                    "headers": [
                        {
                            "name": "Content-Type",
                            "value": "application/x-www-form-urlencoded"
                        }
                    ]
                },
                {
                    "_id": "req_2",
                    "_type": "request",
                    "url": "{{base_url}}/signals/latest",
                    "name": "Get Latest Signals",
                    "method": "GET",
                    "parameters": [
                        {
                            "name": "limit",
                            "value": "10"
                        },
                        {
                            "name": "min_reliability",
                            "value": "80"
                        }
                    ],
                    "headers": [
                        {
                            "name": "Authorization",
                            "value": "Bearer {{access_token}}"
                        }
                    ]
                }
            ]
        }

    def _generate_client_guide_content(self) -> str:
        """Generate client integration guide"""
        return """# Client Integration Guide

This guide provides comprehensive information for integrating with the AI Cash Revolution API.

## Overview

The AI Cash Revolution API provides access to:
- AI-powered trading signals
- Real-time market data
- User management
- Portfolio tracking
- Performance analytics

## Authentication

### JWT Token Authentication

Most endpoints require JWT token authentication. Include the token in the Authorization header:

```
Authorization: Bearer your_jwt_token_here
```

### API Key Authentication

For programmatic access, you can use API key authentication:

```
X-API-Key: your_api_key_here
```

## Getting Started

### 1. Obtain API Credentials

1. Register an account at https://app.cash-revolution.com
2. Generate API key from dashboard
3. Note your API key and base URL

### 2. Choose Your Integration Method

- **SDK**: Use our pre-built SDKs for Python or JavaScript
- **REST API**: Direct HTTP requests to our REST endpoints
- **WebSocket**: Real-time data streaming (coming soon)

### 3. Make Your First Request

```python
import requests

# Get JWT token
response = requests.post('https://api.cash-revolution.com/auth/token',
                        data={'username': 'your_username', 'password': 'your_password'})
token = response.json()['access_token']

# Get latest signals
headers = {'Authorization': f'Bearer {token}'}
signals = requests.get('https://api.cash-revolution.com/signals/latest?limit=10',
                     headers=headers)
print(signals.json())
```

## SDK Integration

### Python SDK

```python
from cash_revolution import CashRevolutionAPI

# Initialize
api = CashRevolutionAPI(api_key='your_api_key')

# Get signals
signals = api.signals.get_latest(limit=10, min_reliability=80)
for signal in signals:
    print(f"{signal.symbol}: {signal.signal_type} at {signal.entry_price}")
```

### JavaScript SDK

```javascript
const CashRevolutionAPI = require('cash-revolution-sdk');

const api = new CashRevolutionAPI({
    apiKey: 'your_api_key'
});

const signals = await api.signals.getLatest({
    limit: 10,
    minReliability: 80
});

console.log(signals);
```

## Rate Limiting

### Limits by Endpoint Type

- **Authentication**: 5 requests per minute
- **Signal Retrieval**: 100 requests per minute
- **Signal Creation**: 10 requests per hour
- **Market Data**: 60 requests per minute
- **User Management**: 30 requests per minute

### Handling Rate Limits

When you exceed rate limits, the API returns HTTP 429 with retry information:

```json
{
  "error": "RateLimitExceeded",
  "message": "Too many requests",
  "details": {
    "retry_after": 60,
    "limit": "100 per minute"
  }
}
```

### Best Practices

1. **Implement Exponential Backoff**: Wait longer between retries
2. **Cache Responses**: Cache market data and signals locally
3. **Batch Requests**: Use bulk operations when available
4. **Monitor Usage**: Track your API usage in the dashboard

## Error Handling

### Standard Error Format

All errors follow this format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "status_code": 400,
  "category": "ValidationError",
  "severity": "low",
  "details": {},
  "field_errors": [],
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "help_url": "https://docs.cash-revolution.com/errors/validation"
}
```

### Common Errors

- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Insufficient permissions or subscription
- **404 Not Found**: Resource doesn't exist
- **422 Validation Error**: Invalid request data
- **429 Rate Limited**: Too many requests
- **500 Internal Error**: Server error

### Error Handling Best Practices

1. **Log Request IDs**: Include request_id in error reports
2. **Implement Retries**: Retry transient errors with backoff
3. **User-Friendly Messages**: Convert technical errors to user-friendly messages
4. **Graceful Degradation**: Handle API unavailability gracefully

## Security Best Practices

### Token Management

- **Store Securely**: Use secure storage for tokens (not local storage in browsers)
- **Short-lived Tokens**: Use access tokens with short expiration (15 minutes)
- **Refresh Tokens**: Use refresh tokens to obtain new access tokens
- **Revoke Tokens**: Revoke tokens when no longer needed

### API Key Management

- **Environment Variables**: Store API keys in environment variables
- **Access Control**: Restrict API key access to authorized personnel
- **Regular Rotation**: Rotate API keys regularly
- **Monitoring**: Monitor API key usage for suspicious activity

### Data Validation

- **Input Validation**: Validate all inputs before sending to API
- **Output Validation**: Validate API responses before processing
- **Type Checking**: Use proper types for all data
- **Sanitization**: Sanitize user-generated content

## Performance Optimization

### Caching

- **Market Data**: Cache market data locally (refresh every 1-5 seconds)
- **Signals**: Cache signal data (refresh every 5-15 minutes)
- **User Data**: Cache user profile data (refresh every 1-6 hours)
- **Static Data**: Cache rarely-changing data indefinitely

### Connection Management

- **Connection Pooling**: Reuse HTTP connections for multiple requests
- **Timeout Management**: Set appropriate timeouts for different endpoints
- **Retry Logic**: Implement retry logic for transient failures
- **Load Balancing**: Distribute requests across multiple instances if needed

### Batch Operations

- **Bulk Signal Creation**: Create multiple signals in one request
- **Batch Market Data**: Request data for multiple symbols
- **Batch User Updates**: Update multiple user settings at once
- **Bulk Operations**: Use bulk operations where available

## Testing

### Unit Testing

```python
import unittest
from unittest.mock import Mock, patch
from cash_revolution import CashRevolutionAPI

class TestCashRevolutionAPI(unittest.TestCase):
    def setUp(self):
        self.api = CashRevolutionAPI(api_key='test_key')

    @patch('requests.get')
    def test_get_latest_signals(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {'symbol': 'EUR_USD', 'signal_type': 'BUY'}
        ]

        signals = self.api.signals.get_latest(limit=1)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].symbol, 'EUR_USD')

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

1. **Test Environment**: Use sandbox environment for testing
2. **Test Data**: Use test data that doesn't affect production
3. **Rate Limits**: Be aware of rate limits in test environment
4. **Cleanup**: Clean up test data after testing

### Load Testing

1. **Gradual Increase**: Start with low request rates and increase gradually
2. **Monitor Performance**: Track response times and error rates
3. **Identify Bottlenecks**: Find performance bottlenecks in your application
4. **Optimize**: Optimize based on load testing results

## Monitoring and Analytics

### Request Logging

- **Request IDs**: Track request IDs for debugging
- **Response Times**: Monitor API response times
- **Error Rates**: Track error rates and patterns
- **Usage Patterns**: Monitor usage patterns and trends

### Performance Metrics

- **Latency**: Track API call latency
- **Throughput**: Monitor requests per second
- **Error Rates**: Track error percentages
- **Availability**: Monitor API uptime

### Business Metrics

- **Signal Usage**: Track signal usage and effectiveness
- **User Engagement**: Monitor user engagement with signals
- **Revenue**: Track revenue from premium features
- **Retention**: Monitor user retention rates

## Support and Resources

### Documentation

- **API Documentation**: https://docs.cash-revolution.com
- **SDK Documentation**: https://docs.cash-revolution.com/sdk
- **Examples**: https://github.com/cash-revolution/examples
- **Tutorials**: https://docs.cash-revolution.com/tutorials

### Support Channels

- **Email**: support@cash-revolution.com
- **Status Page**: https://status.cash-revolution.com
- **Community**: https://community.cash-revolution.com
- **Issues**: https://github.com/cash-revolution/issues

### Updates and Announcements

- **API Updates**: Subscribe to API update notifications
- **Maintenance**: Check maintenance schedule
- **New Features**: Stay informed about new features
- **Deprecations**: Monitor deprecated features and migration guides

---
*Last updated: $(date)*
"""

    def _generate_quick_start_content(self) -> str:
        """Generate quick start guide"""
        return """# Quick Start Guide

This quick start guide will get you up and running with the AI Cash Revolution API in minutes.

## 1. Get Your API Credentials

1. **Sign Up**: Create an account at [https://app.cash-revolution.com](https://app.cash-revolution.com)
2. **Get API Key**: Navigate to Settings > API Keys and generate your API key
3. **Choose Plan**: Select the plan that fits your needs

## 2. Install SDK (Optional)

### Python
```bash
pip install cash-revolution-sdk
```

### JavaScript/Node.js
```bash
npm install cash-revolution-sdk
```

## 3. Make Your First API Call

### Using Python SDK

```python
from cash_revolution import CashRevolutionAPI

# Initialize API client
api = CashRevolutionAPI(api_key='your_api_key_here')

# Get latest signals
signals = api.signals.get_latest(limit=5)

for signal in signals:
    print(f"{signal.symbol}: {signal.signal_type}")
    print(f"Entry: {signal.entry_price}")
    print(f"Reliability: {signal.reliability}%")
    print("---")
```

### Using JavaScript SDK

```javascript
const CashRevolutionAPI = require('cash-revolution-sdk');

// Initialize API client
const api = new CashRevolutionAPI({
    apiKey: 'your_api_key_here'
});

// Get latest signals
const signals = await api.signals.getLatest({ limit: 5 });

signals.forEach(signal => {
    console.log(`${signal.symbol}: ${signal.signal_type}`);
    console.log(`Entry: ${signal.entry_price}`);
    console.log(`Reliability: ${signal.reliability}%`);
    console.log('---');
});
```

### Using cURL

```bash
# Get latest signals
curl -X GET "https://api.cash-revolution.com/signals/latest?limit=5" \\
  -H "X-API-Key: your_api_key_here"

# Example response
{
  "id": 12345,
  "symbol": "EUR_USD",
  "signal_type": "BUY",
  "entry_price": 1.0850,
  "stop_loss": 1.0820,
  "take_profit": 1.0900,
  "reliability": 85.5,
  "confidence_score": 87.0,
  "risk_level": "MEDIUM",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## 4. Create Your First Signal

```python
# Create a new trading signal
signal_data = {
    "symbol": "EUR_USD",
    "signal_type": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0820,
    "take_profit": 1.0900,
    "reliability": 85.5,
    "confidence_score": 87.0,
    "risk_level": "MEDIUM",
    "timeframe": "H1",
    "ai_analysis": "Strong bullish momentum detected"
}

created_signal = api.signals.create(signal_data)
print(f"Created signal ID: {created_signal.id}")
```

## 5. Get Real-time Market Data

```python
# Get market data for EUR/USD
market_data = api.signals.get_market_data('EUR_USD')

print(f"Current bid: {market_data.bid}")
print(f"Current ask: {market_data.ask}")
print(f"Spread: {market_data.spread}")
print(f"Session: {market_data.session}")
```

## 6. Search Signals

```python
# Search for signals
results = api.signals.search(
    query="EURUSD bullish",
    min_reliability=80,
    page=1,
    per_page=10
)

print(f"Found {len(results)} signals")
```

## 7. Handle Errors

```python
from cash_revolution.exceptions import APIError

try:
    signals = api.signals.get_latest(limit=10)
except APIError as e:
    print(f"API Error: {e.message}")
    print(f"Request ID: {e.request_id}")
    print(f"Help URL: {e.help_url}")
```

## Next Steps

1. **Explore Documentation**: Check out our comprehensive [API documentation](https://docs.cash-revolution.com)
2. **View Examples**: Browse our [example applications](https://github.com/cash-revolution/examples)
3. **Join Community**: Connect with other developers in our [community forum](https://community.cash-revolution.com)
4. **Get Support**: Contact our support team at support@cash-revolution.com

## Common Use Cases

### **Trading Bot Integration**
```python
# Automated trading signal processing
signals = api.signals.get_latest(
    min_reliability=85,
    risk_level="MEDIUM"
)

for signal in signals:
    if signal.signal_type == "BUY":
        execute_buy_order(signal)
    elif signal.signal_type == "SELL":
        execute_sell_order(signal)
```

### **Market Analysis Dashboard**
```python
# Real-time market data for dashboard
symbols = ["EUR_USD", "GBPUSD", "USDJPY", "GOLD"]
market_data = {}

for symbol in symbols:
    market_data[symbol] = api.signals.get_market_data(symbol)
    update_dashboard(symbol, market_data[symbol])
```

### **Signal Performance Tracking**
```python
# Track signal performance over time
signals = api.signals.get_latest(limit=100)
performance_analyzer.add_signals(signals)
performance_metrics = performance_analyzer.get_metrics()
```

## Rate Limits and Quotas

- **Free Plan**: 100 requests/day
- **Basic Plan**: 1,000 requests/day
- **Pro Plan**: 10,000 requests/day
- **Enterprise**: Custom limits

Check your usage in the [dashboard](https://app.cash-revolution.com/dashboard).

## Need Help?

- **Documentation**: https://docs.cash-revolution.com
- **API Reference**: https://docs.cash-revolution.com/api
- **Support**: support@cash-revolution.com
- **Status**: https://status.cash-revolution.com

Happy trading! 🚀

---
*Generated on $(date)*
"""