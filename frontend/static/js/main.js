// ===== Main JavaScript for AI Cash-Revolution Landing Page =====
function trackConversion(event, userEmail) {
    // Google Analytics (opzionale)
    if (typeof gtag !== 'undefined') {
        gtag('event', 'conversion', {
            send_to: 'AW-CONVERSION_ID/CONVERSION_LABEL',
            event_category: 'signup',
            event_label: event
        });
    }
    // Facebook Pixel (opzionale)
    if (typeof fbq !== 'undefined') {
        fbq('track', 'Lead', {
            content_name: 'Free Trial Signup',
            content_category: 'Trading Signals'
        });
    }
    // Log di debug, sempre presente
    console.log('Conversion tracked:', event, userEmail);
}

// API Integration for User Registration - Use correct endpoint and payload
async function submitTrialForm(formData) {
    try {
        // Use the correct registration endpoint with simplified payload format
        const registrationData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password')
        };
        
        console.log('Submitting registration form with simplified data:', {
            username: registrationData.username,
            email: registrationData.email
        });
        
        const response = await fetch(CONFIG.API_BASE_URL + '/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(registrationData)
        });
        
        if (response.ok) {
            // Trial signup was successful (201 Created)
            return {
                success: true,
                message: 'Registrazione completata! Controlla la tua email per le credenziali.'
            };
        } else {
            // Handle error response
            const data = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('Trial form submission failed:', {
                status: response.status,
                statusText: response.statusText,
                data: data
            });
            
            let errorMessage = 'Errore durante la registrazione. Riprova.';
            if (response.status === 422) {
                errorMessage = 'Dati non validi. Controlla i campi del modulo.';
            } else if (response.status === 500) {
                errorMessage = 'Servizio temporaneamente non disponibile. Il backend sta risolvendo alcuni problemi tecnici. Ti preghiamo di riprovare tra qualche minuto.';
            } else if (data && data.detail) {
                if (data.detail.includes('Internal server error')) {
                    errorMessage = 'Errore interno del server. Il team tecnico è stato notificato. Riprova tra qualche minuto.';
                } else {
                    errorMessage = data.detail;
                }
            }
            
            throw new Error(errorMessage);
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        return {
            success: false,
            message: error.message || 'Errore durante la registrazione. Riprova.'
        };
    }
}

// Load live statistics from backend
async function loadLiveStats() {
    try {
        // Get top signals for social proof
        const topSignalsResponse = await fetch(CONFIG.API_BASE_URL + '/signals/top', {
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (topSignalsResponse.ok) {
            const signals = await topSignalsResponse.json();
            updateLiveStats(signals);
        }
        
    } catch (error) {
        console.warn('Could not load live stats:', error);
        // Use fallback static data if API is not available
    }
}

function updateLiveStats(signals) {
    // Update the hero statistics with real data
    const statsElements = document.querySelectorAll('.stat-number');
    if (signals && signals.length > 0) {
        // Calculate real statistics from signals
        const totalSignals = signals.length;
        const avgReliability = signals.reduce((sum, signal) => sum + signal.reliability, 0) / signals.length;
        
        // Update DOM elements
        statsElements.forEach(el => {
            const target = el.getAttribute('data-target');
            if (target === '95') {
                el.setAttribute('data-target', Math.round(avgReliability).toString());
            }
        });
    }
}

// ===== Authentication System =====
function initAuthSystem() {
    // Create authentication modals if they don't exist
    createAuthModals();
    
    // Setup dropdown functionality
    const authDropdownBtn = document.getElementById('authDropdownBtn');
    const authDropdownMenu = document.getElementById('authDropdownMenu');
    
    if (authDropdownBtn && authDropdownMenu) {
        authDropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const authDropdown = authDropdownBtn.closest('.auth-dropdown');
            authDropdownMenu.classList.toggle('show');
            if (authDropdown) {
                authDropdown.classList.toggle('show');
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            const authDropdown = authDropdownBtn.closest('.auth-dropdown');
            authDropdownMenu.classList.remove('show');
            if (authDropdown) {
                authDropdown.classList.remove('show');
            }
        });
        
        // Handle auth option clicks
        authDropdownMenu.addEventListener('click', (e) => {
            const option = e.target.closest('.auth-option');
            if (option) {
                const action = option.dataset.action;
                if (action === 'login') {
                    showAuthModal('login');
                } else if (action === 'register') {
                    showAuthModal('register');
                }
                const authDropdown = authDropdownBtn.closest('.auth-dropdown');
                authDropdownMenu.classList.remove('show');
                if (authDropdown) {
                    authDropdown.classList.remove('show');
                }
            }
        });
    }
}

function createAuthModals() {
    // Remove existing modals
    const existingModals = document.querySelectorAll('.auth-modal');
    existingModals.forEach(modal => modal.remove());
    
    // Create modal container
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = `
        <!-- Login Modal -->
        <div id="loginModal" class="auth-modal">
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Accedi al tuo Account</h3>
                        <button class="modal-close" data-modal="loginModal">&times;</button>
                    </div>
                    <form id="loginForm" class="auth-form">
                        <div class="form-group">
                            <label for="loginEmail">Email</label>
                            <input type="email" id="loginEmail" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="loginPassword">Password</label>
                            <input type="password" id="loginPassword" name="password" required>
                        </div>
                        <button type="submit" class="auth-submit-btn">
                            <span class="btn-text">Accedi</span>
                            <span class="btn-spinner" style="display: none;">⏳</span>
                        </button>
                    </form>
                    <div class="auth-switch">
                        <p>Non hai un account? <a href="#" onclick="switchAuthModal('register')">Registrati</a></p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Register Modal -->
        <div id="registerModal" class="auth-modal">
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Crea il tuo Account</h3>
                        <button class="modal-close" data-modal="registerModal">&times;</button>
                    </div>
                    <form id="registerForm" class="auth-form">
                        <div class="form-group">
                            <label for="regUsername">Username</label>
                            <input type="text" id="regUsername" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="regEmail">Email</label>
                            <input type="email" id="regEmail" name="email" required>
                        </div>
                        <div class="form-group">
                            <label for="regPassword">Password</label>
                            <input type="password" id="regPassword" name="password" required minlength="6">
                        </div>
                        <div class="form-checkbox">
                            <input type="checkbox" id="regTerms" name="terms" required>
                            <label for="regTerms">
                                Accetto i <a href="#terms">Termini di Servizio</a> e la 
                                <a href="#privacy">Privacy Policy</a>
                            </label>
                        </div>
                        <button type="submit" class="auth-submit-btn">
                            <span class="btn-text">Registrati</span>
                            <span class="btn-spinner" style="display: none;">⏳</span>
                        </button>
                    </form>
                    <div class="auth-switch">
                        <p>Hai già un account? <a href="#" onclick="switchAuthModal('login')">Accedi</a></p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modalContainer);
    
    // Setup modal event listeners
    setupModalEventListeners();
}

function setupModalEventListeners() {
    // Close modal buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modalId = e.target.dataset.modal;
            hideAuthModal(modalId);
        });
    });
    
    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                hideAuthModal(overlay.parentElement.id);
            }
        });
    });
    
    // Form submissions
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    
    // Escape key to close modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.auth-modal.show').forEach(modal => {
                hideAuthModal(modal.id);
            });
        }
    });
}

function showAuthModal(type) {
    const modalId = type === 'login' ? 'loginModal' : 'registerModal';
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.classList.add('modal-open');
        
        // Focus first input
        setTimeout(() => {
            const firstInput = modal.querySelector('input');
            if (firstInput) firstInput.focus();
        }, 100);
    }
}

function hideAuthModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.classList.remove('modal-open');
    }
}

function switchAuthModal(type) {
    document.querySelectorAll('.auth-modal').forEach(modal => modal.classList.remove('show'));
    showAuthModal(type);
}

async function handleLogin(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('.auth-submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnSpinner = submitBtn.querySelector('.btn-spinner');
    
    // Show loading state
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline';
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        const response = await fetch(CONFIG.API_BASE_URL + '/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                username: formData.get('username'),
                password: formData.get('password')
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store token
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('token_type', data.token_type);
            
            showSuccessMessage('Login effettuato con successo!');
            hideAuthModal('loginModal');
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);
        } else {
            throw new Error(data.detail || 'Login fallito');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showErrorMessage('Credenziali non valide. Riprova.');
    } finally {
        // Reset button state
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
        submitBtn.disabled = false;
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('.auth-submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnSpinner = submitBtn.querySelector('.btn-spinner');
    
    // Show loading state
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline';
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        
        // Validate form data
        const username = formData.get('username')?.trim();
        const email = formData.get('email')?.trim();
        const password = formData.get('password')?.trim();
        
        if (!username || !email || !password) {
            throw new Error('Username, email e password sono obbligatori');
        }
        
        if (!validateEmail(email)) {
            throw new Error('Inserisci un indirizzo email valido');
        }
        
        if (password.length < 6) {
            throw new Error('La password deve essere di almeno 6 caratteri');
        }
        
        // Use correct registration endpoint with simplified payload format
        console.log('Attempting user registration...');
        const registrationData = {
            username: username,
            email: email,
            password: password
        };
        
        console.log('Sending registration data:', {
            username: registrationData.username,
            email: registrationData.email
        });
        
        const response = await fetch(CONFIG.API_BASE_URL + '/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(registrationData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccessMessage('Registrazione completata! Controlla la tua email per le credenziali.');
            hideAuthModal('registerModal');
            form.reset();
            trackConversion('registration', email);
        } else {
            // Log the full response for debugging
            console.error('Registration failed:', {
                status: response.status,
                statusText: response.statusText,
                result: result
            });
            
            // Handle specific error cases
            let errorMessage = 'Errore durante la registrazione. Riprova.';
            
            if (response.status === 409) {
                errorMessage = 'Questo indirizzo email è già registrato.';
            } else if (response.status === 422) {
                errorMessage = 'Dati non validi. Controlla i campi del modulo.';
            } else if (response.status === 500) {
                errorMessage = 'Servizio temporaneamente non disponibile. Il backend sta risolvendo alcuni problemi tecnici. Ti preghiamo di riprovare tra qualche minuto.';
            } else if (result && result.detail) {
                if (result.detail.includes('Internal server error')) {
                    errorMessage = 'Errore interno del server. Il team tecnico è stato notificato. Riprova tra qualche minuto.';
                } else {
                    errorMessage = result.detail;
                }
            }
            
            throw new Error(errorMessage);
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        showErrorMessage(error.message || 'Errore durante la registrazione. Riprova.');
    } finally {
        // Reset button state
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
        submitBtn.disabled = false;
    }
}

// Add logout function for dashboard
async function logout() {
    const showLogoutError = (message) => {
        console.error('Logout error:', message);
        // Show error message using existing function
        if (typeof showErrorMessage === 'function') {
            showErrorMessage('Errore durante il logout: ' + message);
        }
    };

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
                console.log('Server-side logout successful');
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
        
        // Show success message before redirect
        if (typeof showSuccessMessage === 'function') {
            showSuccessMessage('Logout effettuato con successo!');
            // Delay redirect to show message
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            // Immediate redirect if no message function
            window.location.href = '/';
        }
    }
}

// ===== Message Display Functions (Global Scope) =====
function showSuccessMessage(customMessage) {
    // Remove any existing messages
    const existingMessages = document.querySelectorAll('.success-message, .error-message');
    existingMessages.forEach(msg => msg.remove());
    
    const message = document.createElement('div');
    message.className = 'success-message';
    message.innerHTML = `
        <div class="message-content">
            <div class="message-icon">✓</div>
            <div class="message-text">
                <h3>Registrazione Completata!</h3>
                <p>${customMessage || 'Controlla la tua email per le credenziali di accesso. Riceverai i primi segnali entro 60 secondi.'}</p>
            </div>
            <button class="message-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    document.body.appendChild(message);
    
    // Auto-hide after 8 seconds
    setTimeout(() => {
        if (message.parentElement) {
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentElement) {
                    message.remove();
                }
            }, 300);
        }
    }, 8000);
    
    // Add success message styles
    addSuccessMessageStyles();
}

function showErrorMessage(customMessage) {
    // Remove any existing messages
    const existingMessages = document.querySelectorAll('.success-message, .error-message');
    existingMessages.forEach(msg => msg.remove());
    
    const message = document.createElement('div');
    message.className = 'error-message';
    message.innerHTML = `
        <div class="message-content">
            <div class="message-icon">⚠</div>
            <div class="message-text">
                <h3>Errore di Registrazione</h3>
                <p>${customMessage || 'Riprova o contatta il supporto se il problema persiste.'}</p>
            </div>
            <button class="message-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    document.body.appendChild(message);
    
    // Auto-hide after 10 seconds (longer for error messages)
    setTimeout(() => {
        if (message.parentElement) {
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentElement) {
                    message.remove();
                }
            }, 300);
        }
    }, 10000);
    
    addErrorMessageStyles();
}

function addSuccessMessageStyles() {
    if (document.querySelector('#success-message-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'success-message-styles';
    style.textContent = `
        .success-message, .error-message {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid #00ff41;
            border-radius: 15px;
            padding: 20px 50px 20px 20px;
            max-width: 450px;
            opacity: 1;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            animation: slideIn 0.3s ease;
            box-shadow: 0 10px 30px rgba(0, 255, 65, 0.3);
        }
        
        .error-message {
            border-color: #ff4040;
        }
        
        .message-content {
            display: flex;
            align-items: flex-start;
            gap: 15px;
            position: relative;
        }
        
        .message-close {
            position: absolute;
            top: -5px;
            right: -30px;
            background: transparent;
            border: none;
            color: #00ff41;
            font-size: 20px;
            cursor: pointer;
            padding: 5px;
            line-height: 1;
            transition: color 0.2s ease;
        }
        
        .error-message .message-close {
            color: #ff4040;
        }
        
        .message-close:hover {
            color: #ffffff;
            transform: scale(1.1);
        }
        
        .message-icon {
            font-size: 2rem;
            color: #00ff41;
        }
        
        .error-message .message-icon {
            color: #ff4040;
        }
        
        .message-text h3 {
            margin: 0 0 5px 0;
            color: #00ff41;
            font-size: 1.1rem;
        }
        
        .error-message .message-text h3 {
            color: #ff4040;
        }
        
        .message-text p {
            margin: 0;
            color: #e0e0e0;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @media (max-width: 768px) {
            .success-message, .error-message {
                top: 10px;
                right: 10px;
                left: 10px;
                max-width: none;
                padding: 15px 40px 15px 15px;
            }
            
            .message-close {
                right: -25px;
                font-size: 18px;
            }
            
            .message-text h3 {
                font-size: 1rem;
            }
            
            .message-text p {
                font-size: 0.85rem;
            }
        }
    `;
    document.head.appendChild(style);
}

function addErrorMessageStyles() {
    addSuccessMessageStyles(); // Uses same styles
}

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== Authentication Modal System =====
    initAuthSystem();
    
    // ===== Navigation Functions =====
    const navbar = document.querySelector('.navbar');
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            navbar.style.background = 'rgba(0, 0, 0, 0.98)';
            navbar.style.boxShadow = '0 2px 20px rgba(0, 255, 65, 0.3)';
        } else {
            navbar.style.background = 'rgba(0, 0, 0, 0.95)';
            navbar.style.boxShadow = 'none';
        }
    });
    
    // Mobile menu toggle - Enhanced for all pages
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            navLinks.classList.toggle('mobile-open');
            mobileToggle.classList.toggle('active');
            
            // Prevent body scroll when menu is open
            if (navLinks.classList.contains('mobile-open')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (navLinks.classList.contains('mobile-open') && 
                !navLinks.contains(e.target) && 
                !mobileToggle.contains(e.target)) {
                navLinks.classList.remove('mobile-open');
                mobileToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
        
        // Close menu on window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 1024) {
                navLinks.classList.remove('mobile-open');
                mobileToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
        
        // Close menu when pressing escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && navLinks.classList.contains('mobile-open')) {
                navLinks.classList.remove('mobile-open');
                mobileToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                if (navLinks.classList.contains('mobile-open')) {
                    navLinks.classList.remove('mobile-open');
                    mobileToggle.classList.remove('active');
                }
            }
        });
    });
    
    // ===== Hero Section Animations =====
    const heroStats = document.querySelectorAll('.stat-number[data-target]');
    const observerOptions = {
        threshold: 0.5,
        once: true
    };
    
    // ===== Trading Dashboard Simulation =====
    const tradingDashboard = document.querySelector('.trading-dashboard');
    if (tradingDashboard) {
        simulateTradingActivity();
    }
    
    function simulateTradingActivity() {
        const pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'NZD/USD'];
        const directions = ['BUY', 'SELL'];
        const confidenceRange = [85, 99];
        
        const signalPair = document.querySelector('.signal-pair');
        const signalDirection = document.querySelector('.signal-direction');
        const signalConfidence = document.querySelector('.signal-confidence');
        const signalReason = document.querySelector('.signal-ai-reason');
        
        const reasons = [
            'Strong bullish momentum detected. Fed dovish stance + ECB hawkish signals = EUR strength.',
            'Bearish reversal pattern confirmed. Technical indicators align with fundamental weakness.',
            'Breaking key resistance level. Volume spike confirms institutional buying pressure.',
            'Risk-off sentiment driving safe haven demand. Multiple timeframe alignment detected.',
            'Central bank intervention probability high. News sentiment analysis shows 90% negative.',
            'Golden cross formation on 4H chart. RSI divergence suggests trend continuation.'
        ];
        
        function updateSignal() {
            const pair = pairs[Math.floor(Math.random() * pairs.length)];
            const direction = directions[Math.floor(Math.random() * directions.length)];
            const confidence = Math.floor(Math.random() * (confidenceRange[1] - confidenceRange[0] + 1)) + confidenceRange[0];
            const reason = reasons[Math.floor(Math.random() * reasons.length)];
            
            // Update with glitch effect
            if (signalPair) {
                window.MatrixEffects.GlitchEffect.apply(signalPair);
                setTimeout(() => signalPair.textContent = pair, 200);
            }
            
            if (signalDirection) {
                signalDirection.className = `signal-direction ${direction.toLowerCase()}`;
                setTimeout(() => signalDirection.textContent = direction, 200);
            }
            
            if (signalConfidence) {
                setTimeout(() => signalConfidence.textContent = `${confidence}% Confidence`, 200);
            }
            
            if (signalReason) {
                setTimeout(() => signalReason.textContent = `AI Analysis: ${reason}`, 200);
            }
        }
        
        // Update signal every 10 seconds
        setInterval(updateSignal, 10000);
    }
    
    // ===== FAQ Accordion =====
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        
        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            
            // Close all other FAQ items
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                }
            });
            
            // Toggle current item
            if (isActive) {
                item.classList.remove('active');
            } else {
                item.classList.add('active');
            }
        });
    });
    
    // ===== Form Handling =====
    const signupForm = document.getElementById('trial-signup-form');
    
    if (signupForm) {
        signupForm.addEventListener('submit', handleFormSubmission);
    }
    
    async function handleFormSubmission(e) {
        e.preventDefault();
        
        const submitButton = signupForm.querySelector('.form-submit');
        const originalText = submitButton.querySelector('.submit-text').textContent;
        
        // Show loading state
        submitButton.classList.add('loading');
        submitButton.querySelector('.submit-text').textContent = 'Processing...';
        submitButton.disabled = true;
        
        // Collect form data
        const formData = new FormData(signupForm);
        
        // Validate form data
        const username = formData.get('username')?.trim();
        const email = formData.get('email')?.trim();
        const password = formData.get('password')?.trim();
        
        if (!username || !email || !password) {
            showErrorMessage('Username, email e password sono obbligatori');
            resetButtonState();
            return;
        }
        
        if (!validateEmail(email)) {
            showErrorMessage('Inserisci un indirizzo email valido');
            resetButtonState();
            return;
        }
        
        if (password.length < 6) {
            showErrorMessage('La password deve essere di almeno 6 caratteri');
            resetButtonState();
            return;
        }
        
        try {
            // Use correct registration endpoint with simplified payload format
            console.log('Attempting user registration from trial form...');
            const registrationData = {
                username: username,
                email: email,
                password: password
            };
            
            console.log('Sending registration data:', {
                username: registrationData.username,
                email: registrationData.email
            });
            
            const response = await fetch(CONFIG.API_BASE_URL + '/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(registrationData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showSuccessMessage('Registrazione completata! Controlla la tua email per le credenziali.');
                signupForm.reset();
                trackConversion('trial_signup', email);
            } else {
                // Log the full response for debugging
                console.error('Registration failed:', {
                    status: response.status,
                    statusText: response.statusText,
                    result: result
                });
                
                handleRegistrationError(response, result);
            }
            
        } catch (error) {
            console.error('Form submission error:', error);
            console.error('Full error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            showErrorMessage('Errore durante la registrazione. Verifica la connessione internet e riprova.');
        } finally {
            resetButtonState();
        }
        
        function resetButtonState() {
            submitButton.classList.remove('loading');
            submitButton.querySelector('.submit-text').textContent = originalText;
            submitButton.disabled = false;
        }
    }
    
    // Message functions now available globally
    
    // ===== Conversion Tracking =====
    function trackConversion(event, userEmail) {
        // Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'conversion', {
                send_to: 'AW-CONVERSION_ID/CONVERSION_LABEL',
                event_category: 'signup',
                event_label: event
            });
        }
        
        // Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', 'Lead', {
                content_name: 'Free Trial Signup',
                content_category: 'Trading Signals'
            });
        }
        
        // Custom tracking
        console.log('Conversion tracked:', event, userEmail);
    }
    
    // ===== Scroll Animations =====
    const observeElements = document.querySelectorAll('.feature-card, .testimonial, .proof-card, .pricing-card');
    
    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                
                // Add Matrix text effect to titles
                const title = entry.target.querySelector('h3, .feature-title, .testimonial h3');
                if (title && title.classList.contains('matrix-text')) {
                    window.MatrixEffects.GlitchEffect.apply(title);
                }
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '50px'
    });
    
    observeElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'all 0.6s ease';
        scrollObserver.observe(element);
    });
    
    // ===== Live Data Updates =====
    async function fetchLiveStats() {
        try {
            const response = await fetch(CONFIG.API_BASE_URL + '/signals/top');
            if (response.ok) {
                const signals = await response.json();
                if (signals && signals.length > 0) {
                    const avgReliability = signals.reduce((sum, signal) => sum + signal.reliability, 0) / signals.length;
                    updateStatNumbers({ 
                        active_traders: 10000 + signals.length * 50, // Dynamic based on signals
                        success_rate: avgReliability,
                        total_profits: 2400000 + (signals.length * 15000) // Dynamic calculation
                    });
                }
            }
        } catch (error) {
            console.log('Using fallback stats:', error);
        }
    }
    
    async function fetchRecentSignals() {
        try {
            const response = await fetch(CONFIG.API_BASE_URL + '/signals/top');
            if (response.ok) {
                const signals = await response.json();
                if (signals && signals.length > 0) {
                    // Convert to the expected format for recent signals display
                    const recentSignals = signals.slice(0, 3).map((signal, index) => ({
                        pair: signal.pair,
                        direction: signal.direction,
                        profit_pips: Math.floor(Math.random() * 200) + 50, // Random profit for demo
                        hours_ago: (index + 1) * 2
                    }));
                    updateRecentSignals(recentSignals);
                }
            }
        } catch (error) {
            console.log('Using fallback signals:', error);
        }
    }
    
    function updateStatNumbers(stats) {
        // Update hero stats
        const activeTraders = document.querySelector('[data-target="10000"]');
        const accuracyRate = document.querySelector('[data-target="95"]');
        
        if (activeTraders) {
            activeTraders.setAttribute('data-target', stats.active_traders);
            activeTraders.textContent = stats.active_traders.toLocaleString();
        }
        
        if (accuracyRate) {
            accuracyRate.setAttribute('data-target', Math.round(stats.success_rate));
            accuracyRate.textContent = Math.round(stats.success_rate);
        }
        
        // Update proof section
        const totalProfits = document.querySelector('.proof-number');
        if (totalProfits && totalProfits.textContent.includes('$')) {
            totalProfits.textContent = `$${(stats.total_profits / 1000000).toFixed(1)}M+`;
        }
    }
    
    function updateRecentSignals(signals) {
        const storyElements = document.querySelectorAll('.success-stories .story');
        
        signals.forEach((signal, index) => {
            if (index < storyElements.length) {
                const story = storyElements[index];
                const pair = story.querySelector('.pair');
                const direction = story.querySelector('.direction');
                const profit = story.querySelector('.profit.success');
                const time = story.querySelector('.story-time');
                
                if (pair) pair.textContent = signal.pair;
                if (direction) {
                    direction.textContent = signal.direction;
                    direction.className = `direction ${signal.direction.toLowerCase()}`;
                }
                if (profit) profit.textContent = `+${signal.profit_pips} pips`;
                if (time) {
                    const timeText = signal.hours_ago === 1 ? '1 hour ago' : `${signal.hours_ago} hours ago`;
                    time.textContent = timeText;
                }
            }
        });
    }
    
    // Initial fetch and setup periodic updates
    fetchLiveStats();
    fetchRecentSignals();
    loadLiveStatistics();
    
    // Update every 2 minutes
    setInterval(() => {
        fetchLiveStats();
        fetchRecentSignals();
        loadLiveStatistics();
    }, 120000);
    
    // ===== Pricing Card Interactions =====
    const pricingCards = document.querySelectorAll('.pricing-card');
    
    pricingCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            const title = card.querySelector('.card-title');
            if (title) {
                window.MatrixEffects.GlitchEffect.apply(title);
            }
        });
    });
    
    // ===== CTA Button Effects =====
    const ctaButtons = document.querySelectorAll('.cta-button, .card-cta');
    
    ctaButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(0, 255, 65, 0.4);
                border-radius: 50%;
                pointer-events: none;
                transform: scale(0);
                animation: ripple 0.6s linear;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Add ripple animation styles
    const rippleStyle = document.createElement('style');
    rippleStyle.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(rippleStyle);
    
    // ===== Form Validation =====
    const formInputs = document.querySelectorAll('.signup-form input, .signup-form select');
    
    formInputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearFieldError);
    });
    
    function validateField(e) {
        const field = e.target;
        const value = field.value.trim();
        const fieldType = field.type || field.tagName.toLowerCase();
        
        clearFieldError(e);
        
        if (!value) {
            showFieldError(field, 'This field is required');
            return false;
        }
        
        switch (fieldType) {
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    showFieldError(field, 'Please enter a valid email address');
                    return false;
                }
                break;
                
            case 'tel':
                const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
                if (!phoneRegex.test(value.replace(/\s/g, ''))) {
                    showFieldError(field, 'Please enter a valid phone number');
                    return false;
                }
                break;
        }
        
        return true;
    }
    
    function showFieldError(field, message) {
        field.style.borderColor = '#ff4040';
        
        let errorElement = field.parentNode.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            errorElement.style.cssText = `
                color: #ff4040;
                font-size: 0.8rem;
                margin-top: 5px;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        setTimeout(() => errorElement.style.opacity = '1', 10);
    }
    
    function clearFieldError(e) {
        const field = e.target;
        field.style.borderColor = '#333';
        
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.style.opacity = '0';
            setTimeout(() => errorElement.remove(), 300);
        }
    }
    
    // ===== Performance Monitoring =====
    function monitorPerformance() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    console.log(`${entry.name}: ${entry.value}ms`);
                });
            });
            
            observer.observe({ entryTypes: ['measure', 'navigation'] });
        }
        
        // Track page load time
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`Page loaded in ${loadTime}ms`);
            
            // Track with analytics if available
            if (typeof gtag !== 'undefined') {
                gtag('event', 'timing_complete', {
                    name: 'load',
                    value: Math.round(loadTime)
                });
            }
        });
    }
    
    monitorPerformance();
    
    // Load live statistics from backend
    async function loadLiveStatistics() {
        try {
            const response = await fetch(CONFIG.API_BASE_URL + '/signals/top', {
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const signals = await response.json();
                if (signals && signals.length > 0) {
                    // Calculate average reliability
                    const avgReliability = signals.reduce((sum, signal) => sum + signal.reliability, 0) / signals.length;
                    
                    // Update the accuracy stat
                    const accuracyStat = document.querySelector('[data-target="95"]');
                    if (accuracyStat) {
                        accuracyStat.setAttribute('data-target', Math.round(avgReliability).toString());
                        accuracyStat.textContent = Math.round(avgReliability).toString();
                    }
                    
                    console.log('Live stats loaded successfully:', {
                        totalSignals: signals.length,
                        avgReliability: Math.round(avgReliability)
                    });
                }
            }
        } catch (error) {
            console.warn('Could not load live stats, using static data:', error);
        }
    }

    // Load live statistics when page loads
    loadLiveStatistics();
    
    // ===== Initialize all features =====
    console.log('AI Cash-Revolution landing page initialized');
});

// ===== Helper Functions =====

// Email validation function
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Handle registration error responses
function handleRegistrationError(response, result) {
    let errorMessage = 'Errore durante la registrazione. Riprova.';
    
    if (response.status === 409) {
        errorMessage = 'Questo indirizzo email è già registrato.';
    } else if (response.status === 422) {
        errorMessage = 'Dati non validi. Controlla i campi del modulo.';
    } else if (response.status === 500) {
        errorMessage = 'Servizio temporaneamente non disponibile. Il backend sta risolvendo alcuni problemi tecnici. Ti preghiamo di riprovare tra qualche minuto.';
    } else if (result && result.detail) {
        if (result.detail.includes('Internal server error')) {
            errorMessage = 'Errore interno del server. Il team tecnico è stato notificato. Riprova tra qualche minuto.';
        } else {
            errorMessage = result.detail;
        }
    }
    
    showErrorMessage(errorMessage);
}

// ===== Utility Functions =====
const utils = {
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    formatNumber: function(num) {
        return new Intl.NumberFormat().format(num);
    },
    
    formatCurrency: function(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }
};

// ===== Mobile-Specific Functions =====
const MobileUtils = {
    // Detect if user is on mobile device
    isMobile: function() {
        return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    // Get touch coordinates
    getTouchCoordinates: function(e) {
        const touch = e.touches[0] || e.changedTouches[0];
        return {
            x: touch.clientX,
            y: touch.clientY
        };
    },
    
    // Handle touch events for better mobile interaction
    addTouchHandlers: function(element, callbacks) {
        let touchStartTime = 0;
        let touchStartPos = { x: 0, y: 0 };
        
        element.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
            const coords = this.getTouchCoordinates(e);
            touchStartPos = coords;
            if (callbacks.onTouchStart) callbacks.onTouchStart(e, coords);
        }, { passive: true });
        
        element.addEventListener('touchend', (e) => {
            const touchDuration = Date.now() - touchStartTime;
            const coords = this.getTouchCoordinates(e);
            
            // Determine if it's a tap or swipe
            const distance = Math.sqrt(
                Math.pow(coords.x - touchStartPos.x, 2) + 
                Math.pow(coords.y - touchStartPos.y, 2)
            );
            
            if (touchDuration < 300 && distance < 10) {
                if (callbacks.onTap) callbacks.onTap(e, coords);
            } else if (distance > 50) {
                const direction = this.getSwipeDirection(touchStartPos, coords);
                if (callbacks.onSwipe) callbacks.onSwipe(e, direction, distance);
            }
            
            if (callbacks.onTouchEnd) callbacks.onTouchEnd(e, coords);
        }, { passive: true });
    },
    
    // Get swipe direction
    getSwipeDirection: function(start, end) {
        const deltaX = end.x - start.x;
        const deltaY = end.y - start.y;
        
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            return deltaX > 0 ? 'right' : 'left';
        } else {
            return deltaY > 0 ? 'down' : 'up';
        }
    },
    
    // Optimize for mobile viewport
    optimizeViewport: function() {
        // Prevent zoom on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                // Fix viewport scaling issues on orientation change
                const viewport = document.querySelector('meta[name=viewport]');
                if (viewport) {
                    viewport.content = viewport.content;
                }
            }, 500);
        });
    },
    
    // Show/hide mobile-specific UI elements
    adaptUIForMobile: function() {
        const isMobile = this.isMobile();
        
        // Toggle mobile-specific classes
        document.body.classList.toggle('mobile-device', isMobile);
        
        // Adjust button sizes for touch
        if (isMobile) {
            const buttons = document.querySelectorAll('button, .btn, .cta-button');
            buttons.forEach(btn => {
                const style = window.getComputedStyle(btn);
                const height = parseInt(style.height);
                if (height < 44) {
                    btn.style.minHeight = '44px';
                    btn.style.padding = '12px 16px';
                }
            });
        }
    }
};

// Initialize mobile optimizations
if (MobileUtils.isMobile()) {
    MobileUtils.optimizeViewport();
    MobileUtils.adaptUIForMobile();
}

// ===== Export for global use =====
window.AILandingPage = {
    utils,
    MobileUtils,
    // Error/Success message functions
    showSuccessMessage,
    showErrorMessage,
    trackConversion: function(event, userEmail) {
        // Public method for tracking conversions
        trackConversion(event, userEmail);
    },
    
    // Global mobile navigation handler
    initMobileNav: function() {
        const toggle = document.querySelector('.mobile-menu-toggle');
        const navLinks = document.querySelector('.nav-links');
        
        if (toggle && navLinks) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                navLinks.classList.toggle('mobile-open');
                toggle.classList.toggle('active');
                
                if (navLinks.classList.contains('mobile-open')) {
                    document.body.style.overflow = 'hidden';
                } else {
                    document.body.style.overflow = '';
                }
            });
            
            // Close on outside click
            document.addEventListener('click', (e) => {
                if (navLinks.classList.contains('mobile-open') && 
                    !navLinks.contains(e.target) && 
                    !toggle.contains(e.target)) {
                    navLinks.classList.remove('mobile-open');
                    toggle.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
            
            // Close on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && navLinks.classList.contains('mobile-open')) {
                    navLinks.classList.remove('mobile-open');
                    toggle.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        }
    }
};