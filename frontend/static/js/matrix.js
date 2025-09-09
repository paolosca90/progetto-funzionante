// ===== Matrix Digital Rain Effect =====
class MatrixRain {
    constructor() {
        this.canvas = document.getElementById('matrix-rain');
        this.ctx = this.canvas.getContext('2d');
        this.characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$¥€£¢₹₽₿@#%&*+=<>[]{}|\\';
        this.fontSize = 14;
        this.columns = 0;
        this.drops = [];
        this.animationId = null;
        
        this.init();
        this.setupEventListeners();
    }
    
    init() {
        this.resizeCanvas();
        this.initializeDrops();
        this.animate();
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.columns = Math.floor(this.canvas.width / this.fontSize);
        
        // Reinitialize drops when canvas is resized
        this.initializeDrops();
    }
    
    initializeDrops() {
        this.drops = [];
        for(let i = 0; i < this.columns; i++) {
            this.drops[i] = {
                y: Math.random() * this.canvas.height,
                speed: Math.random() * 3 + 1,
                character: this.getRandomCharacter(),
                opacity: Math.random() * 0.5 + 0.5
            };
        }
    }
    
    getRandomCharacter() {
        return this.characters.charAt(Math.floor(Math.random() * this.characters.length));
    }
    
    draw() {
        // Create fade effect
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Set text properties
        this.ctx.font = `${this.fontSize}px 'Source Code Pro', monospace`;
        this.ctx.textAlign = 'center';
        
        // Draw characters
        for(let i = 0; i < this.drops.length; i++) {
            const drop = this.drops[i];
            
            // Create gradient effect
            const gradient = this.ctx.createLinearGradient(
                i * this.fontSize, drop.y - 50,
                i * this.fontSize, drop.y + 50
            );
            gradient.addColorStop(0, `rgba(0, 255, 65, ${drop.opacity * 0.1})`);
            gradient.addColorStop(0.5, `rgba(0, 255, 65, ${drop.opacity})`);
            gradient.addColorStop(1, `rgba(0, 255, 65, ${drop.opacity * 0.1})`);
            
            this.ctx.fillStyle = gradient;
            this.ctx.fillText(
                drop.character,
                i * this.fontSize + this.fontSize / 2,
                drop.y
            );
            
            // Update drop position
            drop.y += drop.speed;
            
            // Reset drop when it goes off screen
            if(drop.y > this.canvas.height + 50) {
                drop.y = -50;
                drop.speed = Math.random() * 3 + 1;
                drop.character = this.getRandomCharacter();
                drop.opacity = Math.random() * 0.5 + 0.5;
            }
            
            // Randomly change character
            if(Math.random() > 0.98) {
                drop.character = this.getRandomCharacter();
            }
        }
    }
    
    animate() {
        this.draw();
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.resizeCanvas();
        });
        
        // Pause animation when tab is not visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (this.animationId) {
                    cancelAnimationFrame(this.animationId);
                    this.animationId = null;
                }
            } else {
                if (!this.animationId) {
                    this.animate();
                }
            }
        });
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        window.removeEventListener('resize', this.resizeCanvas);
    }
}

// ===== Performance Chart Animation =====
class PerformanceChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.data = [];
        this.maxDataPoints = 30;
        this.animationProgress = 0;
        this.targetProgress = 1;
        
        this.generateData();
        this.animate();
    }
    
    generateData() {
        // Generate sample performance data
        this.data = [];
        let value = 100;
        
        for(let i = 0; i < this.maxDataPoints; i++) {
            value += (Math.random() - 0.3) * 20; // Trending upward
            value = Math.max(80, Math.min(200, value)); // Keep in reasonable range
            this.data.push(value);
        }
    }
    
    draw() {
        const { width, height } = this.canvas;
        this.ctx.clearRect(0, 0, width, height);
        
        // Draw grid
        this.ctx.strokeStyle = 'rgba(0, 255, 65, 0.1)';
        this.ctx.lineWidth = 1;
        
        // Vertical lines
        for(let i = 0; i <= 6; i++) {
            const x = (width / 6) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, height);
            this.ctx.stroke();
        }
        
        // Horizontal lines
        for(let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(width, y);
            this.ctx.stroke();
        }
        
        // Draw performance line
        if (this.data.length > 1) {
            const pointCount = Math.floor(this.data.length * this.animationProgress);
            
            if (pointCount > 1) {
                this.ctx.strokeStyle = '#00ff41';
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                
                for(let i = 0; i < pointCount; i++) {
                    const x = (width / (this.data.length - 1)) * i;
                    const y = height - ((this.data[i] - 80) / 120) * height;
                    
                    if (i === 0) {
                        this.ctx.moveTo(x, y);
                    } else {
                        this.ctx.lineTo(x, y);
                    }
                }
                
                this.ctx.stroke();
                
                // Draw glow effect
                this.ctx.shadowColor = '#00ff41';
                this.ctx.shadowBlur = 10;
                this.ctx.stroke();
                this.ctx.shadowBlur = 0;
                
                // Draw data points
                this.ctx.fillStyle = '#00ff41';
                for(let i = 0; i < pointCount; i++) {
                    const x = (width / (this.data.length - 1)) * i;
                    const y = height - ((this.data[i] - 80) / 120) * height;
                    
                    this.ctx.beginPath();
                    this.ctx.arc(x, y, 3, 0, Math.PI * 2);
                    this.ctx.fill();
                }
            }
        }
    }
    
    animate() {
        if (this.animationProgress < this.targetProgress) {
            this.animationProgress += 0.02;
            this.draw();
            requestAnimationFrame(() => this.animate());
        } else {
            this.draw();
        }
    }
}

// ===== Number Counter Animation =====
class NumberCounter {
    static animateCounters() {
        const counters = document.querySelectorAll('[data-target]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = parseInt(entry.target.getAttribute('data-target'));
                    const duration = 2000; // 2 seconds
                    const start = performance.now();
                    const startValue = 0;
                    
                    const animate = (currentTime) => {
                        const elapsed = currentTime - start;
                        const progress = Math.min(elapsed / duration, 1);
                        
                        // Easing function
                        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                        const currentValue = Math.floor(startValue + (target - startValue) * easeOutQuart);
                        
                        entry.target.textContent = currentValue.toLocaleString();
                        
                        if (progress < 1) {
                            requestAnimationFrame(animate);
                        } else {
                            entry.target.textContent = target.toLocaleString();
                        }
                    };
                    
                    requestAnimationFrame(animate);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.5
        });
        
        counters.forEach(counter => observer.observe(counter));
    }
}

// ===== Glitch Effect =====
class GlitchEffect {
    static apply(element, duration = 200) {
        const originalText = element.textContent;
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()';
        
        let iteration = 0;
        const maxIterations = 10;
        
        const interval = setInterval(() => {
            element.textContent = originalText
                .split('')
                .map((char, index) => {
                    if (index < iteration) {
                        return originalText[index];
                    }
                    return characters[Math.floor(Math.random() * characters.length)];
                })
                .join('');
            
            iteration += 1/3;
            
            if (iteration >= originalText.length) {
                clearInterval(interval);
                element.textContent = originalText;
            }
        }, duration / maxIterations);
    }
}

// ===== Matrix Text Effect =====
class MatrixTextEffect {
    static apply(element) {
        const text = element.textContent;
        element.innerHTML = '';
        
        [...text].forEach((char, index) => {
            const span = document.createElement('span');
            span.textContent = char;
            span.style.animationDelay = `${index * 0.1}s`;
            span.classList.add('matrix-char');
            element.appendChild(span);
        });
    }
}

// ===== Particle System =====
class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.maxParticles = 50;
        
        this.init();
    }
    
    init() {
        for(let i = 0; i < this.maxParticles; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                size: Math.random() * 3 + 1,
                opacity: Math.random() * 0.5 + 0.5,
                life: Math.random() * 100 + 50
            });
        }
        
        this.animate();
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach((particle, index) => {
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.life--;
            
            // Wrap around screen
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            // Draw particle
            this.ctx.fillStyle = `rgba(0, 255, 65, ${particle.opacity})`;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Reset particle if life is over
            if (particle.life <= 0) {
                particle.x = Math.random() * this.canvas.width;
                particle.y = Math.random() * this.canvas.height;
                particle.vx = (Math.random() - 0.5) * 2;
                particle.vy = (Math.random() - 0.5) * 2;
                particle.life = Math.random() * 100 + 50;
                particle.opacity = Math.random() * 0.5 + 0.5;
            }
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// ===== Initialize Matrix Effects =====
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Matrix Rain
    const matrixRain = new MatrixRain();
    
    // Initialize Performance Chart
    const performanceChart = new PerformanceChart('performance-chart');
    
    // Initialize Number Counters
    NumberCounter.animateCounters();
    
    // Add Matrix text effects
    document.querySelectorAll('.matrix-text').forEach(element => {
        element.addEventListener('mouseenter', () => {
            GlitchEffect.apply(element);
        });
    });
    
    // Add CSS for matrix character animation
    const style = document.createElement('style');
    style.textContent = `
        .matrix-char {
            display: inline-block;
            animation: matrix-glow 2s infinite;
        }
        
        @keyframes matrix-glow {
            0%, 100% { 
                color: #00ff41;
                text-shadow: 0 0 5px #00ff41;
            }
            50% { 
                color: #ffffff;
                text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41;
            }
        }
    `;
    document.head.appendChild(style);
});

// ===== Export for use in other scripts =====
window.MatrixEffects = {
    MatrixRain,
    PerformanceChart,
    NumberCounter,
    GlitchEffect,
    MatrixTextEffect,
    ParticleSystem
};