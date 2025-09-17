// Configuration for AI Cash-Revolution Frontend
const CONFIG = {
    // Railway Backend URL - Complete API with CORS support
    API_BASE_URL: 'https://web-production-51f67.up.railway.app', // ✅ Railway: Complete backend
    
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

// Helper function to get full API URL
function getApiUrl(endpoint) {
    return CONFIG.API_BASE_URL + CONFIG.ENDPOINTS[endpoint];
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
                window.location.href = '/';
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

// Logout function for all pages
async function logout() {
    try {
        // Call backend logout endpoint with proper URL and error handling
        const token = localStorage.getItem('access_token');
        if (token) {
            console.log('Attempting server-side logout...');
            
            const response = await fetch(CONFIG.API_BASE_URL + '/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
            });
            
            if (!response.ok) {
                // Log the specific error but don't block logout
                console.warn(`Logout endpoint returned ${response.status}: ${response.statusText}`);
            } else {
                const result = await response.json();
                console.log('Server-side logout successful:', result.message);
            }
        }
    } catch (error) {
        console.warn('Logout endpoint error (proceeding with client-side cleanup):', error.message);
    } finally {
        // Always clear client-side data regardless of server response
        console.log('Clearing local storage and redirecting...');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token'); 
        localStorage.removeItem('token_type');
        
        // Show success message if available
        if (typeof showSuccessMessage === 'function') {
            showSuccessMessage('Logout effettuato con successo!');
            // Delay redirect to show message
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            // Create a simple success indicator for pages without showSuccessMessage
            const successDiv = document.createElement('div');
            successDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #00ff41;
                color: black;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 10000;
                font-weight: bold;
                animation: fadeInOut 2s ease-in-out;
            `;
            successDiv.textContent = 'Logout successful!';
            
            // Add fade animation if not exists
            if (!document.querySelector('#logout-animation-style')) {
                const style = document.createElement('style');
                style.id = 'logout-animation-style';
                style.textContent = `
                    @keyframes fadeInOut {
                        0%, 100% { opacity: 0; transform: translateX(100%); }
                        20%, 80% { opacity: 1; transform: translateX(0); }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(successDiv);
            
            // Redirect after showing message
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        }
    }
}

// Export for use in other scripts
window.CONFIG = CONFIG;
window.getApiUrl = getApiUrl;
window.makeApiRequest = makeApiRequest;
window.logout = logout;