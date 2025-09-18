"""
Enhanced Swagger UI Configuration for Interactive API Documentation

This module provides comprehensive Swagger UI customization including:
- Custom themes and styling
- Enhanced documentation presentation
- Interactive testing capabilities
- API key authentication setup
- Example requests and responses
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
import json
import logging

logger = logging.getLogger(__name__)

# Enhanced Swagger UI configuration
SWAGGER_UI_CONFIG = {
    "dom_id": "#swagger-ui",
    "url": "/openapi.json",
    "layout": "StandaloneLayout",
    "deepLinking": True,
    "showExtensions": True,
    "showCommonExtensions": True,
    "docExpansion": "list",
    "defaultModelExpandDepth": 1,
    "defaultModelsExpandDepth": 1,
    "displayOperationId": False,
    "displayRequestDuration": True,
    "filter": True,
    "showRequestHeaders": True,
    "showResponseHeaders": True,
    "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
    "persistAuthorization": True,
    "tryItOutEnabled": True,
    "requestSnippetsEnabled": True,
    "oauth2RedirectUrl": "http://localhost:8000/docs/oauth2-redirect.html",
    "plugins": [
        {
            "name": "SwaggerUIFilter",
            "url": "https://unpkg.com/swagger-ui-filter"
        }
    ],
    "presets": [
        "SwaggerUIBundle.presets.apis",
        "SwaggerUIStandalonePreset"
    ],
    "pluginsOptions": {
        "requestSnippets": {
            "languages": ["curl", "Python", "JavaScript", "C#"]
        }
    }
}

# Custom Swagger UI CSS for enhanced styling
CUSTOM_SWAGGER_CSS = """
/* Custom Swagger UI Styling */
.swagger-ui {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}

.swagger-ui .topbar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.swagger-ui .info {
    margin: 15px 0;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}

.swagger-ui .info .title {
    color: #2c3e50;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 10px;
}

.swagger-ui .info .description {
    color: #34495e;
    line-height: 1.6;
}

.swagger-ui .opblock {
    border-radius: 8px;
    margin-bottom: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

.swagger-ui .opblock .opblock-summary {
    border-radius: 8px 8px 0 0;
}

.swagger-ui .opblock .opblock-summary-method {
    border-radius: 8px 0 0 8px;
    font-weight: 600;
    text-transform: uppercase;
}

.swagger-ui .opblock.get .opblock-summary-method {
    background: #61affe;
    color: white;
}

.swagger-ui .opblock.post .opblock-summary-method {
    background: #49cc90;
    color: white;
}

.swagger-ui .opblock.put .opblock-summary-method {
    background: #fca130;
    color: white;
}

.swagger-ui .opblock.delete .opblock-summary-method {
    background: #f93e3e;
    color: white;
}

.swagger-ui .opblock .opblock-summary-description {
    color: #2c3e50;
    font-weight: 500;
}

.swagger-ui .parameter__name {
    color: #2c3e50;
    font-weight: 600;
}

.swagger-ui .parameter__type {
    color: #667eea;
    font-weight: 500;
}

.swagger-ui .response-col_status {
    color: white;
    font-weight: 600;
    text-align: center;
    border-radius: 4px;
}

.swagger-ui .response-col_status .response-undocumented {
    background: #95a5a6;
}

.swagger-ui .response-col_status .response-200 {
    background: #49cc90;
}

.swagger-ui .response-col_status .response-201 {
    background: #61affe;
}

.swagger-ui .response-col_status .response-400 {
    background: #fca130;
}

.swagger-ui .response-col_status .response-401 {
    background: #f93e3e;
}

.swagger-ui .response-col_status .response-404 {
    background: #f93e3e;
}

.swagger-ui .response-col_status .response-500 {
    background: #7f8c8d;
}

.swagger-ui .btn {
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.swagger-ui .btn.authorize {
    background: #667eea;
    color: white;
}

.swagger-ui .btn.authorize:hover {
    background: #5a67d8;
    color: white;
}

.swagger-ui .btn.try-out {
    background: #49cc90;
    color: white;
}

.swagger-ui .btn.try-out:hover {
    background: #3fb77e;
    color: white;
}

.swagger-ui .execute-wrapper .btn.execute {
    background: #667eea;
    color: white;
}

.swagger-ui .execute-wrapper .btn.execute:hover {
    background: #5a67d8;
    color: white;
}

/* Custom API Information Section */
.api-info {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    border-radius: 12px;
    margin: 20px 0;
    text-align: center;
}

.api-info h1 {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 15px;
}

.api-info p {
    font-size: 16px;
    line-height: 1.6;
    opacity: 0.9;
}

.api-info .features {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 20px;
    flex-wrap: wrap;
}

.api-info .feature {
    background: rgba(255,255,255,0.1);
    padding: 10px 20px;
    border-radius: 25px;
    font-size: 14px;
    backdrop-filter: blur(10px);
}

/* Authentication Section */
.auth-section {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    border-left: 4px solid #667eea;
}

.auth-section h3 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.auth-section p {
    color: #34495e;
    line-height: 1.6;
}

.auth-section .auth-method {
    background: white;
    border-radius: 6px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid #e9ecef;
}

.auth-section .auth-method h4 {
    color: #667eea;
    margin-bottom: 10px;
}

.auth-section .auth-method code {
    background: #f1f3f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', monospace;
}

/* Quick Start Section */
.quick-start {
    background: #e8f5e8;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    border-left: 4px solid #49cc90;
}

.quick-start h3 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.quick-start ol {
    color: #34495e;
    line-height: 1.8;
}

.quick-start code {
    background: #f1f3f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', monospace;
}

/* Rate Limiting Info */
.rate-limiting {
    background: #fff3cd;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    border-left: 4px solid #ffc107;
}

.rate-limiting h3 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.rate-limiting .limit-info {
    background: white;
    border-radius: 6px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid #ffeaa7;
}

.rate-limiting .limit-info strong {
    color: #856404;
}

/* Footer */
.swagger-footer {
    text-align: center;
    padding: 30px;
    background: #f8f9fa;
    border-top: 1px solid #e9ecef;
    margin-top: 40px;
}

.swagger-footer p {
    color: #6c757d;
    margin-bottom: 10px;
}

.swagger-footer .version {
    background: #667eea;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 14px;
    display: inline-block;
}
"""

# Custom JavaScript for enhanced Swagger UI
CUSTOM_SWAGGER_JS = """
// Enhanced Swagger UI functionality
window.addEventListener('load', function() {
    // Add custom authentication helper
    const originalAuthorize = window.ui.authActions.authorize;
    window.ui.authActions.authorize = function(security) {
        console.log('Custom authorization handler:', security);
        return originalAuthorize.call(this, security);
    };

    // Add request/response formatting
    const formatJSON = function(obj) {
        return JSON.stringify(obj, null, 2);
    };

    // Add example request builder
    const buildExampleRequest = function(method, path, params) {
        const example = {
            method: method.toUpperCase(),
            url: window.location.origin + path,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
            }
        };

        if (params && Object.keys(params).length > 0) {
            example.data = params;
        }

        return example;
    };

    // Add custom event listeners
    document.addEventListener('DOMContentLoaded', function() {
        // Add API key input enhancement
        const authInputs = document.querySelectorAll('.auth-container input');
        authInputs.forEach(input => {
            input.addEventListener('input', function(e) {
                if (e.target.type === 'password') {
                    e.target.type = 'text';
                    setTimeout(() => {
                        e.target.type = 'password';
                    }, 2000);
                }
            });
        });

        // Add try-it-out enhancement
        const tryItButtons = document.querySelectorAll('.try-out');
        tryItButtons.forEach(button => {
            button.addEventListener('click', function() {
                setTimeout(() => {
                    const executeButtons = document.querySelectorAll('.execute');
                    executeButtons.forEach(exeButton => {
                        exeButton.style.background = '#667eea';
                        exeButton.style.color = 'white';
                    });
                }, 100);
            });
        });
    });

    // Console logging for debugging
    console.log('Enhanced Swagger UI loaded successfully');
});
"""

# Custom HTML template for enhanced documentation
ENHANCED_DOCS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Cash Revolution Trading API - Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <link rel="stylesheet" type="text/css" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" />
    <style>{custom_css}</style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        const ui = SwaggerUIBundle({{ui_config}});
        window.ui = ui;
    </script>
    <script>{custom_js}</script>
</body>
</html>
"""

class SwaggerUIEnhancer:
    """Enhanced Swagger UI generator with custom styling and functionality"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.config = SWAGGER_UI_CONFIG.copy()

    def get_enhanced_swagger_ui_html(self, request: Request) -> HTMLResponse:
        """Get enhanced Swagger UI HTML with custom styling and functionality

        Args:
            request: The incoming request

        Returns:
            HTMLResponse: Enhanced Swagger UI HTML
        """
        # Update config with current request URL
        self.config["url"] = f"{request.url.scheme}://{request.url.netloc}/openapi.json"
        self.config["oauth2RedirectUrl"] = f"{request.url.scheme}://{request.url.netloc}/docs/oauth2-redirect.html"

        # Prepare UI config as JSON string
        ui_config_json = json.dumps(self.config, indent=2)

        # Create enhanced HTML
        html_content = ENHANCED_DOCS_TEMPLATE.format(
            custom_css=CUSTOM_SWAGGER_CSS,
            ui_config=ui_config_json,
            custom_js=CUSTOM_SWAGGER_JS
        )

        return HTMLResponse(content=html_content)

    def get_api_info_html(self) -> HTMLResponse:
        """Get API information HTML page

        Returns:
            HTMLResponse: API information page HTML
        """
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>API Information - AI Cash Revolution Trading API</title>
            <style>
                body {{
                    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
                    margin: 0;
                    padding: 40px;
                    background: #f8f9fa;
                    color: #2c3e50;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .header h1 {{
                    font-size: 36px;
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .header p {{
                    font-size: 18px;
                    color: #6c757d;
                }}
                .card {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                }}
                .card h3 {{
                    color: #667eea;
                    margin-bottom: 20px;
                    font-size: 24px;
                }}
                .card p {{
                    line-height: 1.6;
                    color: #34495e;
                }}
                .card ul {{
                    margin: 15px 0;
                    padding-left: 20px;
                }}
                .card li {{
                    margin-bottom: 8px;
                }}
                .stats {{
                    display: flex;
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                .stat {{
                    flex: 1;
                    background: #667eea;
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .stat h4 {{
                    font-size: 24px;
                    margin-bottom: 5px;
                }}
                .stat p {{
                    margin: 0;
                    opacity: 0.9;
                }}
                .btn {{
                    background: #667eea;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    text-decoration: none;
                    display: inline-block;
                    font-weight: 500;
                    transition: background 0.2s;
                }}
                .btn:hover {{
                    background: #5a67d8;
                    color: white;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    margin-top: 40px;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 AI Cash Revolution Trading API</h1>
                    <p>Professional AI-powered trading signals platform with comprehensive documentation</p>
                </div>

                <div class="stats">
                    <div class="stat">
                        <h4>50+</h4>
                        <p>API Endpoints</p>
                    </div>
                    <div class="stat">
                        <h4>4</h4>
                        <p>Authentication Methods</p>
                    </div>
                    <div class="stat">
                        <h4>10+</h4>
                        <p>SDK Languages</p>
                    </div>
                    <div class="stat">
                        <h4>99.9%</h4>
                        <p>Uptime SLA</p>
                    </div>
                </div>

                <div class="card">
                    <h3>📚 Documentation</h3>
                    <p>Explore our comprehensive API documentation and interactive testing tools:</p>
                    <ul>
                        <li><a href="/docs" class="btn">Interactive Swagger UI</a> - Test API endpoints directly</li>
                        <li><a href="/redoc" class="btn">ReDoc Documentation</a> - Developer-friendly documentation</li>
                        <li><a href="/api/docs/preview" class="btn">API Preview</a> - Quick API overview</li>
                        <li><a href="/api/docs/generate" class="btn">Generate SDK</a> - Download client libraries</li>
                    </ul>
                </div>

                <div class="card">
                    <h3>🔐 Authentication</h3>
                    <p>Multiple authentication methods to suit your needs:</p>
                    <ul>
                        <li><strong>JWT Bearer Tokens</strong> - Ideal for web and mobile applications</li>
                        <li><strong>API Keys</strong> - Perfect for server-to-server integration</li>
                        <li><strong>OAuth2</strong> - Standard third-party application authentication</li>
                        <li><strong>Basic Auth</strong> - Legacy system support</li>
                    </ul>
                </div>

                <div class="card">
                    <h3>📊 Key Features</h3>
                    <ul>
                        <li>Real-time trading signals with AI-powered analysis</li>
                        <li>Comprehensive market data from OANDA</li>
                        <li>Advanced risk management and position sizing</li>
                        <li>Multi-timeframe technical analysis</li>
                        <li>Performance tracking and analytics</li>
                        <li>Webhook support for real-time updates</li>
                    </ul>
                </div>

                <div class="card">
                    <h3>🛠️ Developer Tools</h3>
                    <ul>
                        <li>Interactive API documentation with live testing</li>
                        <li>Automatic SDK generation for multiple languages</li>
                        <li>Comprehensive error handling and examples</li>
                        <li>Rate limiting and usage monitoring</li>
                        <li>Webhook integration capabilities</li>
                    </ul>
                </div>

                <div class="card">
                    <h3>📞 Support</h3>
                    <p>Need help? Our support team is here to assist you:</p>
                    <ul>
                        <li><strong>Email:</strong> support@cash-revolution.com</li>
                        <li><strong>Documentation:</strong> <a href="https://docs.cash-revolution.com">docs.cash-revolution.com</a></li>
                        <li><strong>Status:</strong> <a href="/health">System Health</a></li>
                        <li><strong>API Status:</strong> <a href="/health">API Status</a></li>
                    </ul>
                </div>

                <div class="footer">
                    <p>© 2024 AI Cash Revolution Trading API v2.0.1</p>
                    <p>Built with FastAPI, OANDA Integration, and Google Gemini AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    def add_custom_routes(self):
        """Add custom documentation routes to the FastAPI application"""

        @self.app.get("/docs/enhanced", response_class=HTMLResponse)
        async def enhanced_docs(request: Request):
            """Enhanced Swagger UI with custom styling and functionality"""
            return self.get_enhanced_swagger_ui_html(request)

        @self.app.get("/docs/info", response_class=HTMLResponse)
        async def api_info():
            """API information and quick start guide"""
            return self.get_api_info_html()

        @self.app.get("/docs/oauth2-redirect.html", response_class=HTMLResponse)
        async def oauth2_redirect():
            """OAuth2 redirect page for Swagger UI"""
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <title>OAuth2 Redirect</title>
            </head>
            <body>
                <script>
                    window.opener.postMessage(window.location.href, window.location.origin);
                    window.close();
                </script>
                <p>Redirecting... Please close this window.</p>
            </body>
            </html>
            """)

        return self.app