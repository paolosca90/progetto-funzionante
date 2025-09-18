# Step 1: API Credentials Configuration Guide

## 🎯 Objective
Configure the missing API credentials that are critical for your AI trading system to achieve production readiness.

## 📋 Current Status
- **OANDA_API_KEY**: Currently set to "test_key" ❌
- **OANDA_ACCOUNT_ID**: Currently set to "test_account" ❌
- **GEMINI_API_KEY**: Currently set to "test_gemini_key" ❌

## 🔧 Required Actions

### 1. OANDA API Credentials Setup

#### Get Your OANDA Credentials:
1. **Visit**: https://www.oanda.com/demo-account/tpa/personal_token
2. **Create a Demo Account** (if you don't have one)
3. **Generate API Access Token**:
   - Log in to your OANDA account
   - Navigate to Account Management → API Access
   - Generate a new Personal Access Token
   - Copy the token (starts with "xxxx-xxxx-xxxx-xxxx")

4. **Find Your Account ID**:
   - In your OANDA dashboard
   - Look for your Account Number (typically format: xxx-xxx-xxxxxx-xxx)

#### Configure OANDA Environment:
- **For Testing**: Use `"demo"` environment
- **For Live Trading**: Use `"live"` environment

### 2. Google Gemini API Key Setup

#### Get Your Gemini API Key:
1. **Visit**: https://makersuite.google.com/app/apikey
2. **Create a new API Key**:
   - Click "Create API Key"
   - Choose your project or create a new one
   - Copy the generated key
3. **Enable Gemini API**:
   - Go to Google Cloud Console
   - Enable "Generative Language API"

### 3. Environment Configuration

#### Option A: Update .env File Directly
```bash
# Edit your .env file:
OANDA_API_KEY="your_real_oanda_api_key_here"
OANDA_ACCOUNT_ID="your_real_account_id_here"
OANDA_ENVIRONMENT="demo"
GEMINI_API_KEY="your_real_gemini_api_key_here"
```

#### Option B: Use Setup Script
```bash
# Run the automated setup script
python setup_api_credentials.py
```

## 🧪 Validation Steps

### After Configuration, Run:
```bash
# Validate the setup
python validate_api_setup.py

# Test OANDA connectivity
python test_oanda_connection.py

# Test Gemini AI integration
python test_gemini_integration.py
```

## ⚡ Quick Start Commands

### For Immediate Testing:
```bash
# 1. Set environment variables (Windows)
set OANDA_API_KEY="your_api_key_here"
set OANDA_ACCOUNT_ID="your_account_id_here"
set GEMINI_API_KEY="your_gemini_key_here"

# 2. Run validation
python validate_api_setup.py

# 3. Test connectivity
python test_oanda_connection.py
```

## 🔍 Troubleshooting

### Common Issues:

1. **Invalid API Key**:
   - Verify key format (should be "xxxx-xxxx-xxxx-xxxx")
   - Ensure key is copied correctly without extra spaces

2. **Account ID Format**:
   - Should be in format: xxx-xxx-xxxxxx-xxx
   - Verify no extra characters or spaces

3. **Gemini API Issues**:
   - Ensure Generative Language API is enabled
   - Check API key restrictions
   - Verify billing is enabled in Google Cloud

4. **Network Issues**:
   - Check internet connectivity
   - Verify firewall settings
   - Check for proxy requirements

## 🎯 Success Criteria

The setup is successful when:
- ✅ OANDA API connectivity test passes
- ✅ Gemini AI integration test passes
- ✅ Environment validation passes
- ✅ All tests show "PRODUCTION READY" status

## ⏱️ Estimated Time: 15-30 minutes

## 📞 Support Resources

- **OANDA API Documentation**: https://developer.oanda.com/
- **Gemini API Documentation**: https://ai.google.dev/docs
- **OANDA Support**: https://www.oanda.com/support/
- **Google Cloud Support**: https://cloud.google.com/support

---

**Note**: Always use demo environment for initial testing. Switch to live environment only after thorough validation and when ready for real trading.