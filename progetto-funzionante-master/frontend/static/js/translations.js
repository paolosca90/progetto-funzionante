// Multi-language translation system for AI Cash-Revolution
const translations = {
    it: {
        // Navigation
        'nav.dashboard': 'Dashboard',
        'nav.signals': 'Segnali',
        'nav.account': 'Account',
        'nav.mt5': 'MT5',
        'nav.features': 'Caratteristiche',
        'nav.proof': 'Prova',
        'nav.pricing': 'Prezzi',
        'nav.contact': 'Contatti',
        'nav.trial': 'Prova Gratuita',

        // Hero section
        'hero.badge': 'Rivoluzione del Trading Alimentata da IA',
        'hero.title': 'Sblocca La <span class="matrix-text">Matrix</span> del <br>Successo nel Trading',
        'hero.subtitle': 'Unisciti a oltre 10.000 trader che utilizzano i nostri segnali alimentati da IA con <strong>95% di accuratezza</strong>. Integrazione MT5 in tempo reale, notifiche istantanee e spiegazioni IA per ogni segnale.',
        'hero.stats.traders': 'Trader Attivi',
        'hero.stats.accuracy': '% Tasso di Accuratezza',
        'hero.stats.support': 'Ore di Supporto',
        'hero.cta.main': 'Inizia Prova Gratuita 7 Giorni',
        'hero.cta.sub': 'Nessuna Carta di Credito Richiesta',
        'hero.trust.security': 'Sicurezza di Livello Bancario',
        'hero.trust.setup': 'Configurazione Istantanea',
        'hero.trust.integration': 'Integrazione MT5',

        // Social proof
        'social.title': 'Fiducia dei Trader di Tutto il Mondo',
        'social.subtitle': 'Unisciti alle migliaia di persone che hanno già sbloccato la matrix del trading profittevole',

        // Testimonials
        'testimonials.1.content': '"Sono passato dal perdere 500€/mese al guadagnare 3.200€ di profitto nella mia prima settimana. Le spiegazioni dell\'IA mi hanno aiutato a capire PERCHÉ ogni segnale funziona."',
        'testimonials.1.name': 'Marco Rodriguez',
        'testimonials.1.title': 'Day Trader, Miami',
        'testimonials.2.content': '"Il 95% di accuratezza non è pubblicità ingannevole - è reale. Ho monitorato ogni segnale per 3 mesi. L\'integrazione MT5 è perfetta."',
        'testimonials.2.name': 'Sara Kim',
        'testimonials.2.title': 'Forex Trader, Singapore',
        'testimonials.3.content': '"L\'IA non si limita a dare segnali - ti insegna. Ho imparato di più in 2 mesi che in 2 anni di corsi di trading tradizionali."',
        'testimonials.3.name': 'James Davidson',
        'testimonials.3.title': 'Trader Professionale, Londra',
        'testimonials.verified': '✓ Risultato Verificato',

        // Stats
        'stats.profits': 'Profitti Totali Generati',
        'stats.countries': 'Paesi Serviti',
        'stats.uptime': 'Garanzia di Uptime',

        // Features
        'features.title': 'Perché AI Cash-Revolution <span class="matrix-text">Domina</span>',
        'features.subtitle': 'La tecnologia IA avanzata incontra l\'infrastruttura di trading professionale',
        'features.ai.title': 'Analisi Alimentata da IA',
        'features.ai.description': 'Le nostre reti neurali elaborano oltre 10.000 punti dati al secondo, analizzando il sentiment del mercato, l\'impatto delle notizie e i pattern tecnici per generare segnali ad alta affidabilità.',
        'features.ai.highlight': '95% Tasso di Accuratezza',
        'features.mt5.title': 'Integrazione MT5 in Tempo Reale',
        'features.mt5.description': 'Integrazione diretta con MetaTrader 5. I segnali appaiono istantaneamente nella tua piattaforma con punti di entrata, stop loss e take profit calcolati automaticamente.',
        'features.mt5.highlight': 'Esecuzione Istantanea',
        'features.risk.title': 'Gestione Intelligente del Rischio',
        'features.risk.description': 'L\'IA calcola la dimensione ottimale delle posizioni basandosi sul saldo del tuo account, tolleranza al rischio e volatilità del mercato. Non rischiare mai più di quello che puoi permetterti.',
        'features.risk.highlight': 'Adattato al Rischio',
        'features.alerts.title': 'Avvisi Multi-Piattaforma',
        'features.alerts.description': 'Ricevi segnali tramite notifiche push, SMS, email e Telegram. Non perdere mai un\'opportunità profittevole, anche quando sei lontano dal computer.',
        'features.alerts.highlight': 'Monitoraggio 24/7',
        'features.analytics.title': 'Analisi delle Performance',
        'features.analytics.description': 'Statistiche dettagliate tracciano il tuo tasso di vincita, rendimenti medi e metriche di rischio. Comprendi le tue performance e ottimizza la tua strategia di trading.',
        'features.analytics.highlight': 'Basato sui Dati',
        'features.education.title': 'Educazione al Trading IA',
        'features.education.description': 'Ogni segnale viene fornito con spiegazioni dettagliate dell\'IA. Impara PERCHÉ il trade funziona, migliorando la tua comprensione del mercato e le tue abilità di trading.',
        'features.education.highlight': 'Educativo',

        // Pricing
        'pricing.title': 'Scegli il Tuo <span class="matrix-text">Percorso</span>',
        'pricing.subtitle': 'Inizia gratis, aggiorna quando vedi i risultati',
        'pricing.trial.badge': 'INIZIO SENZA RISCHI',
        'pricing.trial.title': 'Prova Gratuita 7 Giorni',
        'pricing.trial.price': '0€',
        'pricing.trial.period': 'per 7 giorni',
        'pricing.trial.features': [
            '✓ Accesso completo a tutti i segnali',
            '✓ Integrazione MT5 inclusa',
            '✓ Spiegazioni IA per ogni trade',
            '✓ Notifiche in tempo reale',
            '✓ Analisi delle performance',
            '✓ Supporto 24/7'
        ],
        'pricing.trial.cta': 'Inizia Prova Gratuita',
        'pricing.trial.subcta': 'Nessuna Carta di Credito Richiesta',

        'pricing.pro.badge': 'PIÙ POPOLARE',
        'pricing.pro.title': 'Pro Trader',
        'pricing.pro.price': '97€',
        'pricing.pro.period': 'al mese',
        'pricing.pro.features': [
            '✓ Tutto della Prova Gratuita',
            '✓ Consegna segnali prioritaria',
            '✓ Gestione avanzata del rischio',
            '✓ Preferenze avvisi personalizzate',
            '✓ Canale supporto VIP',
            '✓ Chiamate strategiche mensili'
        ],
        'pricing.pro.cta': 'Aggiorna a Pro',
        'pricing.pro.subcta': 'Dopo la prova gratuita',

        'pricing.enterprise.badge': 'ISTITUZIONI',
        'pricing.enterprise.title': 'Enterprise',
        'pricing.enterprise.price': 'Personalizzato',
        'pricing.enterprise.period': 'prezzo',
        'pricing.enterprise.features': [
            '✓ Tutto di Pro',
            '✓ Soluzioni white-label',
            '✓ Integrazione API personalizzata',
            '✓ Account manager dedicato',
            '✓ Parametri di rischio personalizzati',
            '✓ Conformità istituzionale'
        ],
        'pricing.enterprise.cta': 'Contatta le Vendite',
        'pricing.enterprise.subcta': 'Soluzioni personalizzate',

        // Form
        'form.title': 'Inizia la Tua Prova Gratuita',
        'form.subtitle': 'Nessuna carta di credito richiesta • Accesso istantaneo',
        'form.name': 'Nome Completo',
        'form.email': 'Indirizzo Email',
        'form.phone': 'Numero di Telefono',
        'form.experience': 'Esperienza di Trading',
        'form.experience.select': 'Seleziona il tuo livello',
        'form.experience.beginner': 'Principiante (0-1 anni)',
        'form.experience.intermediate': 'Intermedio (1-5 anni)',
        'form.experience.advanced': 'Avanzato (5+ anni)',
        'form.terms': 'Accetto i <a href="#terms">Termini di Servizio</a> e la <a href="#privacy">Privacy Policy</a>',
        'form.submit': 'Inizia Prova Gratuita',
        'form.security': '🔒 Crittografato SSL',
        'form.privacy': '🛡️ Privacy Protetta',

        // Proof section
        'proof.title': 'I Numeri Non <span class="matrix-text">Mentono</span>',
        'proof.subtitle': 'Risultati reali da trader reali che utilizzano la nostra piattaforma',
        'proof.performance.title': 'Performance Ultimi 30 Giorni',
        'proof.performance.status': 'DATI LIVE',
        'proof.stats.total': 'Segnali Totali',
        'proof.stats.winning': 'Segnali Vincenti',
        'proof.stats.success': 'Tasso di Successo',
        'proof.stats.return': 'Rendimento Medio',
        'proof.stories.title': 'Storie di Successo Recenti',
        'proof.stories.time1': '2 ore fa',
        'proof.stories.time2': '6 ore fa',
        'proof.stories.time3': '1 giorno fa',
        'proof.risk': '<strong>Avviso di Rischio:</strong> Il trading comporta rischi sostanziali e non è adatto a tutti gli investitori. Le performance passate non garantiscono risultati futuri. Tutti i dati di performance sono verificati e controllati.',

        // Pricing
        'pricing.trial.feature1': '✓ Accesso completo a tutti i segnali',
        'pricing.trial.feature2': '✓ Integrazione MT5 inclusa',
        'pricing.trial.feature3': '✓ Spiegazioni IA per ogni trade',
        'pricing.trial.feature4': '✓ Notifiche in tempo reale',
        'pricing.trial.feature5': '✓ Analisi delle performance',
        'pricing.trial.feature6': '✓ Supporto 24/7',
        'pricing.pro.feature1': '✓ Tutto della Prova Gratuita',
        'pricing.pro.feature2': '✓ Consegna segnali prioritaria',
        'pricing.pro.feature3': '✓ Gestione avanzata del rischio',
        'pricing.pro.feature4': '✓ Preferenze avvisi personalizzate',
        'pricing.pro.feature5': '✓ Canale supporto VIP',
        'pricing.pro.feature6': '✓ Chiamate strategiche mensili',

        // Trial section
        'trial.title': 'Pronto ad <span class="matrix-text">Entrare nella Matrix</span>?',
        'trial.subtitle': 'Unisciti a oltre 10.000 trader che hanno già sbloccato profitti alimentati dall\'IA',
        'trial.benefit1': '<strong>Accesso Istantaneo</strong><br>Inizia a ricevere segnali entro 60 secondi',
        'trial.benefit2': '<strong>Configurazione Facile</strong><br>Connetti il tuo MT5 in meno di 5 minuti',
        'trial.benefit3': '<strong>Senza Rischi</strong><br>Nessuna carta di credito richiesta per la prova',

        // Footer
        'footer.description': 'Rivoluzionando il trading con segnali alimentati dall\'IA e analisi di mercato avanzate. Unisciti alla matrix finanziaria e sblocca il tuo potenziale di profitto.',
        'footer.platform': 'Piattaforma',
        'footer.features': 'Caratteristiche',
        'footer.pricing': 'Prezzi',
        'footer.trial': 'Prova Gratuita',
        'footer.faq': 'FAQ',
        'footer.support': 'Supporto',
        'footer.contact': 'Contattaci',
        'footer.help': 'Centro Assistenza',
        'footer.docs': 'Documentazione API',
        'footer.status': 'Stato Sistema',
        'footer.legal': 'Legale',
        'footer.terms': 'Termini di Servizio',
        'footer.privacy': 'Privacy Policy',
        'footer.risk': 'Informativa Rischio',
        'footer.compliance': 'Conformità',
        'footer.connect': 'Connetti',
        'footer.copyright': '© 2024 AI Cash-Revolution. Tutti i diritti riservati.',
        'footer.warning': 'Avviso di Rischio: Il trading comporta un rischio sostanziale di perdite e non è adatto a tutti gli investitori.',

        // FAQ
        'faq.title': 'Domande <span class="matrix-text">Frequenti</span>',
        'faq.1.question': 'Quanto sono accurati i vostri segnali di trading IA?',
        'faq.1.answer': 'Il nostro sistema IA mantiene un tasso di accuratezza del 95% su tutte le principali coppie di valute. Questo viene raggiunto attraverso algoritmi di machine learning avanzati che elaborano oltre 10.000 punti dati al secondo, inclusi indicatori tecnici, sentiment del mercato, eventi di notizie e dati economici.',
        'faq.2.question': 'Ho bisogno di esperienza di trading per usare questo servizio?',
        'faq.2.answer': 'Non è richiesta esperienza precedente. La nostra IA fornisce spiegazioni dettagliate per ogni segnale, aiutandoti a comprendere il ragionamento dietro ogni trade. Offriamo anche risorse educative e supporto per aiutare i principianti a iniziare in sicurezza.',
        'faq.3.question': 'Quanto velocemente ricevo i segnali di trading?',
        'faq.3.answer': 'I segnali vengono consegnati istantaneamente attraverso canali multipli: notifiche push, SMS, email e direttamente alla tua piattaforma MT5. Il nostro sistema opera 24/5 durante le ore di mercato con latenza in millisecondi.',
        'faq.4.question': 'I miei soldi e dati sono sicuri?',
        'faq.4.answer': 'Utilizziamo crittografia e protocolli di sicurezza di livello bancario. Non abbiamo mai accesso ai fondi del tuo conto di trading - il nostro sistema invia solo segnali alla tua piattaforma MT5. Tutti i dati personali sono protetti sotto la conformità GDPR.',
        'faq.5.question': 'Posso cancellare il mio abbonamento in qualsiasi momento?',
        'faq.5.answer': 'Sì, puoi cancellare il tuo abbonamento in qualsiasi momento senza penali.',
        'faq.6.question': 'Cosa è incluso nella prova gratuita di 7 giorni?',
        'faq.6.answer': 'La prova gratuita include accesso completo a tutte le funzionalità: segnali IA, integrazione MT5, analisi delle performance, contenuti educativi e supporto 24/7. Non è richiesta carta di credito per iniziare.'
    },

    en: {
        // Navigation
        'nav.dashboard': 'Dashboard',
        'nav.signals': 'Signals',
        'nav.account': 'Account',
        'nav.mt5': 'MT5',
        'nav.features': 'Features',
        'nav.proof': 'Proof',
        'nav.pricing': 'Pricing',
        'nav.contact': 'Contact',
        'nav.trial': 'Free Trial',

        // Hero section
        'hero.badge': 'AI-Powered Trading Revolution',
        'hero.title': 'Unlock The <span class="matrix-text">Matrix</span> of <br>Trading Success',
        'hero.subtitle': 'Join 10,000+ traders using our AI-powered signals with <strong>95% accuracy</strong>. Real-time MT5 integration, instant notifications, and AI explanations for every signal.',
        'hero.stats.traders': 'Active Traders',
        'hero.stats.accuracy': '% Accuracy Rate',
        'hero.stats.support': 'Hours Support',
        'hero.cta.main': 'Start 7-Day Free Trial',
        'hero.cta.sub': 'No Credit Card Required',
        'hero.trust.security': 'Bank-Level Security',
        'hero.trust.setup': 'Instant Setup',
        'hero.trust.integration': 'MT5 Integration',

        // Social proof
        'social.title': 'Trusted by Traders Worldwide',
        'social.subtitle': 'Join thousands who\'ve already unlocked the matrix of profitable trading',

        // Testimonials
        'testimonials.1.content': '"I went from losing $500/month to making $3,200 profit in my first week. The AI explanations helped me understand WHY each signal works."',
        'testimonials.1.name': 'Marcus Rodriguez',
        'testimonials.1.title': 'Day Trader, Miami',
        'testimonials.2.content': '"95% accuracy isn\'t marketing hype - it\'s real. I\'ve tracked every signal for 3 months. The MT5 integration is seamless."',
        'testimonials.2.name': 'Sarah Kim',
        'testimonials.2.title': 'Forex Trader, Singapore',
        'testimonials.3.content': '"The AI doesn\'t just give signals - it teaches you. I\'ve learned more in 2 months than 2 years of traditional trading courses."',
        'testimonials.3.name': 'James Davidson',
        'testimonials.3.title': 'Professional Trader, London',
        'testimonials.verified': '✓ Verified Result',

        // Stats
        'stats.profits': 'Total Profits Generated',
        'stats.countries': 'Countries Served',
        'stats.uptime': 'Uptime Guarantee',

        // Features
        'features.title': 'Why AI Cash-Revolution <span class="matrix-text">Dominates</span>',
        'features.subtitle': 'Advanced AI technology meets professional trading infrastructure',
        'features.ai.title': 'AI-Powered Analysis',
        'features.ai.description': 'Our neural networks process 10,000+ data points per second, analyzing market sentiment, news impact, and technical patterns to generate high-confidence signals.',
        'features.ai.highlight': '95% Accuracy Rate',
        'features.mt5.title': 'Real-Time MT5 Integration',
        'features.mt5.description': 'Direct integration with MetaTrader 5. Signals appear instantly in your platform with entry points, stop losses, and take profits automatically calculated.',
        'features.mt5.highlight': 'Instant Execution',
        'features.risk.title': 'Smart Risk Management',
        'features.risk.description': 'AI calculates optimal position sizing based on your account balance, risk tolerance, and market volatility. Never risk more than you can afford.',
        'features.risk.highlight': 'Risk-Adjusted',
        'features.alerts.title': 'Multi-Platform Alerts',
        'features.alerts.description': 'Receive signals via push notifications, SMS, email, and Telegram. Never miss a profitable opportunity, even when away from your computer.',
        'features.alerts.highlight': '24/7 Monitoring',
        'features.analytics.title': 'Performance Analytics',
        'features.analytics.description': 'Detailed statistics track your win rate, average returns, and risk metrics. Understand your performance and optimize your trading strategy.',
        'features.analytics.highlight': 'Data-Driven',
        'features.education.title': 'AI Trading Education',
        'features.education.description': 'Each signal comes with detailed AI explanations. Learn WHY the trade works, improving your market understanding and trading skills.',
        'features.education.highlight': 'Educational'
    },

    es: {
        // Navigation
        'nav.dashboard': 'Panel',
        'nav.signals': 'Señales',
        'nav.account': 'Cuenta',
        'nav.mt5': 'MT5',
        'nav.features': 'Características',
        'nav.proof': 'Prueba',
        'nav.pricing': 'Precios',
        'nav.contact': 'Contacto',
        'nav.trial': 'Prueba Gratis',

        // Hero section
        'hero.badge': 'Revolución de Trading Impulsada por IA',
        'hero.title': 'Desbloquea La <span class="matrix-text">Matrix</span> del <br>Éxito en Trading',
        'hero.subtitle': 'Únete a más de 10,000 traders que usan nuestras señales impulsadas por IA con <strong>95% de precisión</strong>. Integración MT5 en tiempo real, notificaciones instantáneas y explicaciones de IA para cada señal.',
        'hero.stats.traders': 'Traders Activos',
        'hero.stats.accuracy': '% Tasa de Precisión',
        'hero.stats.support': 'Horas de Soporte',
        'hero.cta.main': 'Iniciar Prueba Gratis de 7 Días',
        'hero.cta.sub': 'Sin Tarjeta de Crédito Requerida',
        'hero.trust.security': 'Seguridad de Nivel Bancario',
        'hero.trust.setup': 'Configuración Instantánea',
        'hero.trust.integration': 'Integración MT5',

        // Social proof
        'social.title': 'Confiado por Traders de Todo el Mundo',
        'social.subtitle': 'Únete a miles que ya han desbloqueado la matrix del trading rentable',

        // Features
        'features.title': 'Por Qué AI Cash-Revolution <span class="matrix-text">Domina</span>',
        'features.subtitle': 'Tecnología IA avanzada se encuentra con infraestructura de trading profesional'
    },

    fr: {
        // Navigation
        'nav.dashboard': 'Tableau de Bord',
        'nav.signals': 'Signaux',
        'nav.account': 'Compte',
        'nav.mt5': 'MT5',
        'nav.features': 'Fonctionnalités',
        'nav.proof': 'Preuve',
        'nav.pricing': 'Tarifs',
        'nav.contact': 'Contact',
        'nav.trial': 'Essai Gratuit',

        // Hero section
        'hero.badge': 'Révolution Trading Alimentée par IA',
        'hero.title': 'Débloquez La <span class="matrix-text">Matrix</span> du <br>Succès Trading',
        'hero.subtitle': 'Rejoignez plus de 10 000 traders utilisant nos signaux alimentés par IA avec <strong>95% de précision</strong>. Intégration MT5 en temps réel, notifications instantanées et explications IA pour chaque signal.',
        'hero.stats.traders': 'Traders Actifs',
        'hero.stats.accuracy': '% Taux de Précision',
        'hero.stats.support': 'Heures de Support',
        'hero.cta.main': 'Commencer Essai Gratuit 7 Jours',
        'hero.cta.sub': 'Aucune Carte de Crédit Requise',
        'hero.trust.security': 'Sécurité de Niveau Bancaire',
        'hero.trust.setup': 'Configuration Instantanée',
        'hero.trust.integration': 'Intégration MT5',

        // Social proof
        'social.title': 'Approuvé par les Traders du Monde Entier',
        'social.subtitle': 'Rejoignez des milliers de personnes qui ont déjà débloqué la matrix du trading rentable',

        // Features
        'features.title': 'Pourquoi AI Cash-Revolution <span class="matrix-text">Domine</span>',
        'features.subtitle': 'La technologie IA avancée rencontre l\'infrastructure de trading professionnelle'
    }
};

// Language management system
class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('ai-cash-revolution-language') || 'it';
        this.init();
    }

    init() {
        this.updateLanguageDisplay();
        this.translatePage();
        this.bindEvents();
    }

    bindEvents() {
        const languageBtn = document.getElementById('languageBtn');
        const languageMenu = document.getElementById('languageMenu');
        const languageOptions = document.querySelectorAll('.language-option');

        if (languageBtn && languageMenu) {
            languageBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                languageMenu.classList.toggle('show');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                languageMenu.classList.remove('show');
            });

            languageMenu.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        languageOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = option.getAttribute('data-lang');
                this.changeLanguage(lang);
                if (languageMenu) {
                    languageMenu.classList.remove('show');
                }
            });
        });
    }

    changeLanguage(lang) {
        if (translations[lang]) {
            this.currentLanguage = lang;
            localStorage.setItem('ai-cash-revolution-language', lang);
            this.updateLanguageDisplay();
            this.translatePage();
        }
    }

    updateLanguageDisplay() {
        const languageBtn = document.getElementById('languageBtn');
        const flagMap = {
            'it': '🇮🇹',
            'en': '🇺🇸',
            'es': '🇪🇸',
            'fr': '🇫🇷'
        };
        const codeMap = {
            'it': 'IT',
            'en': 'EN',
            'es': 'ES',
            'fr': 'FR'
        };

        if (languageBtn) {
            const flagSpan = languageBtn.querySelector('.flag');
            const codeSpan = languageBtn.querySelector('.lang-code');
            
            if (flagSpan && codeSpan) {
                flagSpan.textContent = flagMap[this.currentLanguage] || '🇮🇹';
                codeSpan.textContent = codeMap[this.currentLanguage] || 'IT';
            }
        }
    }

    translatePage() {
        const currentTranslations = translations[this.currentLanguage] || translations.it;
        
        // Translate elements with data-translate attribute
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            const translation = currentTranslations[key];
            
            if (translation) {
                if (element.hasAttribute('data-translate-html')) {
                    element.innerHTML = translation;
                } else {
                    element.textContent = translation;
                }
            }
        });

        // Handle special cases like forms
        this.translateForms(currentTranslations);
    }

    translateForms(translations) {
        // Translate form labels and placeholders
        const formElements = {
            '#fullName': 'form.name',
            '#email': 'form.email',
            '#phone': 'form.phone',
            '#experience': 'form.experience'
        };

        Object.entries(formElements).forEach(([selector, key]) => {
            const element = document.querySelector(selector);
            const label = element?.previousElementSibling;
            
            if (label?.tagName === 'LABEL' && translations[key]) {
                label.textContent = translations[key];
            }
        });

        // Translate select options
        const experienceSelect = document.getElementById('experience');
        if (experienceSelect && translations['form.experience.select']) {
            const options = experienceSelect.options;
            if (options[0]) options[0].textContent = translations['form.experience.select'];
            if (options[1] && translations['form.experience.beginner']) options[1].textContent = translations['form.experience.beginner'];
            if (options[2] && translations['form.experience.intermediate']) options[2].textContent = translations['form.experience.intermediate'];
            if (options[3] && translations['form.experience.advanced']) options[3].textContent = translations['form.experience.advanced'];
        }

        // Translate form buttons
        const submitBtn = document.querySelector('.form-submit .submit-text');
        if (submitBtn && translations['form.submit']) {
            submitBtn.textContent = translations['form.submit'];
        }
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }

    getTranslation(key) {
        const currentTranslations = translations[this.currentLanguage] || translations.it;
        return currentTranslations[key] || key;
    }
}

// Initialize language manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.languageManager = new LanguageManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { translations, LanguageManager };
}
