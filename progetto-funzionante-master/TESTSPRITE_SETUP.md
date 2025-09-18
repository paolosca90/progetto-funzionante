# Testsprite MCP Server Setup and Usage Guide

## Overview

Testsprite is an AI-powered testing automation platform that integrates with Claude Code via the Model Context Protocol (MCP). It provides automated software testing capabilities including web UI testing, API testing, and end-to-end testing workflows.

## Installation Completed ✅

The Testsprite MCP server has been successfully installed on your system:

- **Package**: `@testsprite/testsprite-mcp@0.0.13`
- **Location**: Global npm installation
- **API Key**: Configured and ready to use

## Quick Start

### Method 1: Using the Batch Script (Recommended)

1. **Start the Testsprite Server:**
   ```batch
   # Navigate to your project directory
   cd C:\Users\USER\Desktop\progetto-funzionante-master

   # Run the startup script
   start-testsprite.bat
   ```

2. **The server will start on** `http://localhost:60712` (or similar port)

3. **Use in Claude Code:**
   - The MCP server is configured as `testsprite`
   - Available tools will appear automatically in your Claude Code session

### Method 2: Manual Start

1. **Set environment variable:**
   ```batch
   set TESTSPRITE_API_KEY=sk-user-Bhf0vIgrk_JZXzl9wNxpxMm7dRUgn6conR8HdMZNsoPGhlVkU4VU7isSLz6GiwwZDrm_7rnJ4sPUbU1l4Dj75Mrtww6oS2O7KG8JJtAW5g0uaRa37BxzsuJN0Q2Nvdf30QI
   ```

2. **Start the server:**
   ```batch
   testsprite-mcp-plugin server
   ```

## Available Testing Capabilities

### 1. Web UI Testing (Playwright Integration)
- Automated browser testing
- Form filling and submission
- Click interactions and navigation
- Screenshot capture
- Page content validation

### 2. API Testing
- REST API endpoint testing
- Authentication handling (Bearer tokens, API keys, Basic auth)
- Request/response validation
- Error scenario testing

### 3. Test Configuration Options
- **Backend Testing**: Test server APIs and endpoints
- **Frontend Testing**: Test web applications and user interfaces
- **Scope Options**: Test entire codebase or only recent changes (git diff)

## Configuration

### Authentication Types Supported
- **Bearer Token**: JWT or OAuth tokens
- **API Key**: Custom header-based authentication
- **Basic Auth**: Username/password authentication
- **Public**: No authentication required

### Test Account Setup
- Optional test account credentials for login testing
- Supports both frontend and backend authentication scenarios

### Project Integration
- **Local Development Port**: Specify your local server port (e.g., 3000)
- **Product Specification**: Upload PRD documents for intelligent test generation
- **Git Integration**: Automatically detect code changes for targeted testing

## Usage Examples

### Basic Web Testing
```javascript
// Ask Claude to:
"Test the login functionality on my web app at localhost:3000"
"Take screenshots of the checkout process"
"Validate form submissions and error handling"
```

### API Testing
```javascript
// Ask Claude to:
"Test the REST API endpoints for user authentication"
"Validate API responses with different authentication methods"
"Test error scenarios and edge cases"
```

### Integration Testing
```javascript
// Ask Claude to:
"Run end-to-end tests for the user registration flow"
"Test database integration through the API layer"
"Validate payment processing workflows"
```

## File Locations

- **Main Script**: `C:\Users\USER\Desktop\progetto-funzionante-master\start-testsprite.bat`
- **MCP Configuration**: Stored in Claude Code's local config
- **Package**: `@testsprite/testsprite-mcp` (global npm)

## Troubleshooting

### Common Issues

1. **Server Won't Start**
   - Ensure the API key environment variable is set
   - Check if port 60712 is available
   - Verify npm package installation

2. **Claude Code Can't Connect**
   - Make sure the Testsprite server is running
   - Check MCP server configuration in Claude Code
   - Verify network connectivity to localhost

3. **Test Failures**
   - Ensure your local development server is running
   - Verify authentication credentials are correct
   - Check product specification documents are properly formatted

### Reset Configuration

```batch
# Remove MCP server configuration
claude mcp remove testsprite -s local

# Re-add the server
claude mcp add testsprite testsprite-mcp-plugin server
```

## API Key Information

Your Testsprite API key is configured and ready to use:
- **Key Length**: 184 characters
- **Prefix**: `sk-user-`
- **Status**: ✅ Active and configured

## Support

- **Testsprite Documentation**: Available through the web interface at `http://localhost:60712`
- **Claude Code MCP Commands**: Use `claude mcp --help` for management commands
- **Package Issues**: Report to `@testsprite/testsprite-mcp` npm package

## Next Steps

1. **Start the Testsprite server** using the provided batch script
2. **Begin using testing commands** in your Claude Code sessions
3. **Configure your test scenarios** with authentication and project details
4. **Generate comprehensive test suites** for your applications

---

**Note**: The Testsprite MCP server provides powerful automated testing capabilities. Always ensure you have proper authorization before testing any applications or APIs.