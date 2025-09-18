import requests
import os
from datetime import datetime, timedelta

def send_registration_email(to_email, username):
    """
    Invia l'email di benvenuto con riepilogo accesso tramite la REST API di Resend.
    """
    resend_api_key = os.getenv('RESEND_API_KEY', 're_7Zrgq4ei_5iC1z17Z9aE1sWyWbTATc7AJ')
    from_email = os.getenv('FROM_EMAIL', 'support@cash-revolution.com')
    trial_end_date = (datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y')
    login_url = "https://www.cash-revolution.com/login.html"
    now = datetime.now().strftime('%d/%m/%Y alle %H:%M')

    html_body = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0a0a0a; color: #e0e0e0; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg,#1a1a1a,#2d2d2d); border:2px solid #00ff41; border-radius:15px; padding:30px;">
        <h1 style="color:#00ff41; text-align:center; font-size:24px; margin-bottom:20px;">
          Benvenuto su AI Cash-Revolution!
        </h1>
        <p style="font-size:16px;">Ciao <strong style="color:#00ff41;">{username}</strong>,<br>
        la tua registrazione è stata completata con successo.<br>
        Il <strong>trial gratuito di 7 giorni</strong> è ora attivo!</p>
        
        <div style="margin: 30px 0 25px 0; background: #191c1d; border:1px solid #00ff41; border-radius:8px; padding:16px 22px;">
          <h3 style="color:#00ff41; margin-top:0; text-align:center;"> I TUOI DATI DI ACCESSO</h3>
          <table style="width:100%; color:#e0e0e0; font-size:15px;">
            <tr><td style="padding:6px; color:#00ff41; font-weight:bold;">Username:</td><td style="padding:6px;">{username}</td></tr>
            <tr><td style="padding:6px; color:#00ff41; font-weight:bold;">Email:</td><td style="padding:6px;">{to_email}</td></tr>
            <tr><td style="padding:6px; color:#00ff41; font-weight:bold;">Password:</td><td style="padding:6px;">La password scelta in fase di registrazione</td></tr>
            <tr><td style="padding:6px; color:#00ff41; font-weight:bold;">Stato:</td><td style="padding:6px;"><span style="color:#00ff41; font-weight:bold;">TRIAL ATTIVO</span></td></tr>
            <tr><td style="padding:6px; color:#00ff41; font-weight:bold;">Trial scade il:</td><td style="padding:6px; font-weight:bold;">{trial_end_date}</td></tr>
          </table>
        </div>
        
        <div style="text-align:center;margin:32px 0;">
          <a href="{login_url}" style="display:inline-block; background:linear-gradient(90deg,#00ff41,#00cc33); color:#000; text-decoration:none; padding:15px 37px; border-radius:25px; font-weight:bold; font-size:17px;">
             Fai login nel tuo account
          </a>
        </div>
        
        <div style="background: #2a2a2a; border-radius: 8px; padding: 13px 15px; margin: 18px 0;">
          <h4 style="color:#00ff41; margin-top:0;">- Cosa puoi fare da subito:</h4>
          <ul style="padding-left: 22px; line-height: 1.7;">
            <li>- Ricevi segnali di trading AI in tempo reale</li>
            <li>- Gestisci il tuo profilo e lo status abbonamento</li>
            <li>- Configura MT5 per trading automatico</li>
            <li>- Prova tutte le funzionalità Premium per 7 giorni</li>
          </ul>
        </div>
        
        <p style="font-size:13px; background: #1a1a1a; padding:10px; border-radius:8px; margin-bottom:18px;">
          <strong style="color:#00ff41;">📞 Supporto:</strong> Per assistenza tecnica o domande, rispondi a questa email oppure scrivi a <a href="mailto:{from_email}" style="color:#00ff41;">{from_email}</a>
        </p>
        
        <hr style="border:none; border-top:1px solid #333; margin:20px 0;">
        <p style="text-align:center; font-size:12px; color:#888;">
          AI Cash-Revolution – Trading Automatizzato<br>
          Account creato il {now}<br>
          Questa email è inviata automaticamente, non rispondere per richieste amministrative.
        </p>
      </div>
    </div>
    """
    
    # Plain text fallback (per sicurezza)
    text_body = f"""
Ciao {username},

La tua registrazione su AI Cash-Revolution è avvenuta con successo!
Trial gratuito di 7 giorni attivo.

DATI DI ACCESSO:
- Username: {username}
- Email: {to_email}
- Password: (quella scelta nella registrazione)
- Stato: TRIAL ATTIVO
- Trial scade il: {trial_end_date}

Accedi al login: {login_url}

Per assistenza: {from_email}

AI Cash-Revolution - Trading Automatizzato
Account creato il {now}
"""

    data = {
        "from": from_email,
        "to": [to_email],
        "subject": " AI Cash-Revolution - I tuoi dati di accesso sono pronti!",
        "html": html_body,
        "text": text_body,
    }

    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post("https://api.resend.com/emails", json=data, headers=headers, timeout=15)
        resp.raise_for_status()
        print(f"- Email di benvenuto inviata con Resend a {to_email}")
        return True
    except Exception as e:
        print(f"❌ Errore invio Resend: {e}")
        return False


def send_password_reset_email(to_email, username, reset_token):
    """
    Invia l'email per il reset della password tramite la REST API di Resend.
    """
    resend_api_key = os.getenv('RESEND_API_KEY', 're_7Zrgq4ei_5iC1z17Z9aE1sWyWbTATc7AJ')
    from_email = os.getenv('FROM_EMAIL', 'support@cash-revolution.com')
    reset_url = f"https://www.cash-revolution.com/reset-password.html?token={reset_token}"
    now = datetime.now().strftime('%d/%m/%Y alle %H:%M')

    html_body = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0a0a0a; color: #e0e0e0; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg,#1a1a1a,#2d2d2d); border:2px solid #ff6b35; border-radius:15px; padding:30px;">
        <h1 style="color:#ff6b35; text-align:center; font-size:24px; margin-bottom:20px;">
          Reset Password - AI Cash-Revolution
        </h1>
        <p style="font-size:16px;">Ciao <strong style="color:#ff6b35;">{username}</strong>,<br>
        hai richiesto il reset della tua password.<br>
        Clicca il link qui sotto per impostare una nuova password:</p>
        
        <div style="text-align:center;margin:32px 0;">
          <a href="{reset_url}" style="display:inline-block; background:linear-gradient(90deg,#ff6b35,#e55a2b); color:#fff; text-decoration:none; padding:15px 37px; border-radius:25px; font-weight:bold; font-size:17px;">
             Reset Password
          </a>
        </div>
        
        <div style="background: #2a2a2a; border-radius: 8px; padding: 13px 15px; margin: 18px 0;">
          <h4 style="color:#ff6b35; margin-top:0;">⚠️ Importante:</h4>
          <ul style="padding-left: 22px; line-height: 1.7;">
            <li>Questo link è valido per <strong>1 ora</strong> dalla richiesta</li>
            <li>Se non hai richiesto questo reset, ignora questa email</li>
            <li>Per sicurezza, effettua il reset solo da dispositivi fidati</li>
          </ul>
        </div>
        
        <p style="font-size:13px; background: #1a1a1a; padding:10px; border-radius:8px; margin-bottom:18px;">
          <strong style="color:#ff6b35;">📞 Supporto:</strong> Per assistenza tecnica, scrivi a <a href="mailto:{from_email}" style="color:#ff6b35;">{from_email}</a>
        </p>
        
        <hr style="border:none; border-top:1px solid #333; margin:20px 0;">
        <p style="text-align:center; font-size:12px; color:#888;">
          AI Cash-Revolution – Trading Automatizzato<br>
          Reset richiesto il {now}<br>
          Se non hai effettuato questa richiesta, contatta il supporto.
        </p>
      </div>
    </div>
    """
    
    # Plain text fallback
    text_body = f"""
Ciao {username},

Hai richiesto il reset della password per AI Cash-Revolution.

Reset Link: {reset_url}

IMPORTANTE:
- Questo link è valido per 1 ora dalla richiesta
- Se non hai richiesto questo reset, ignora questa email
- Per sicurezza, effettua il reset solo da dispositivi fidati

Per assistenza: {from_email}

AI Cash-Revolution - Trading Automatizzato
Reset richiesto il {now}
"""

    data = {
        "from": from_email,
        "to": [to_email],
        "subject": "🔑 Reset Password - AI Cash-Revolution",
        "html": html_body,
        "text": text_body,
    }

    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post("https://api.resend.com/emails", json=data, headers=headers, timeout=15)
        resp.raise_for_status()
        print(f"- Email reset password inviata con Resend a {to_email}")
        return True
    except Exception as e:
        print(f"❌ Errore invio email reset: {e}")
        return False
