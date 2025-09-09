// Configuration for AI Cash-Revolution Frontend
const CONFIG = {
    // Railway Backend URL - Complete API with CORS support
    API_BASE_URL: 'https://web-production-51f67.up.railway.app', // ✅ Railway: Complete backend
    
    // VPS Backend URL - Future ML and signals processing
    VPS_BASE_URL: 'http://ai.cash-revolution.com:8001', // ⏳ VPS: ML engine (future)
    
    // API Endpoints
    ENDPOINTS: {
        // Authentication
        register: '/register',
        login: '/token',
        me: '/me',
        
        // Signals
        topSignals: '/signals/top',
        userSignals: '/signals',
        
        // MT5 Integration
        mt5Connect: '/mt5/connect',
        mt5Status: '/mt5/status'
    },
    
    // Request configuration
    REQUEST_CONFIG: {
        timeout: 10000, // 10 seconds
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    }
};

// Helper function to get full API URL (Railway for everything for now)
function getApiUrl(endpoint) {
    // For now, use Railway for everything until VPS has all endpoints
    return CONFIG.API_BASE_URL + CONFIG.ENDPOINTS[endpoint];
}

// Helper function to make requests to VPS
async function makeVPSRequest(endpoint, options = {}) {
    const url = CONFIG.VPS_BASE_URL + endpoint;
    
    const config = {
        ...CONFIG.REQUEST_CONFIG,
        ...options,
        headers: {
            ...CONFIG.REQUEST_CONFIG.headers,
            ...(options.headers || {})
        }
    };
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_CONFIG.timeout);
        
        const response = await fetch(url, {
            ...config,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`VPS HTTP error! status: ${response.status} - ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('VPS Request timeout - please check your connection');
        }
        console.error(`VPS Request failed for ${endpoint}:`, error);
        throw error;
    }
}

// Helper function to make authenticated requests with proper error handling
async function makeApiRequest(endpoint, options = {}) {
    const url = getApiUrl(endpoint);
    const token = localStorage.getItem('access_token');
    
    const config = {
        ...CONFIG.REQUEST_CONFIG,
        ...options,
        headers: {
            ...CONFIG.REQUEST_CONFIG.headers,
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...(options.headers || {})
        }
    };
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_CONFIG.timeout);
        
        const response = await fetch(url, {
            ...config,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.status === 401) {
            // Token expired - redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') {
                window.location.href = 'index.html';
            }
            throw new Error('Authentication expired');
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Request timeout - please check your connection');
        }
        console.error(`API Request failed for ${endpoint}:`, error);
        throw error;
    }
}

// Export for use in other scripts
window.CONFIG = CONFIG;
window.getApiUrl = getApiUrl;
window.makeApiRequest = makeApiRequest;
window.makeVPSRequest = makeVPSRequest;