import os
import datetime
import cloudscraper
import smtplib
from email.mime.text import MIMEText
import requests

# ========= CONFIG =========
URL = os.getenv("RDV_URL")  # variable d'environnement sur Railway
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_TO = os.getenv("EMAIL_TO")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# fichier log local
LOG_FILE = "alerte_rdv.log"
STATE_FILE = "alerte_state.txt"


# ========= UTILS =========
def log_event(message: str):
    """Écrit un message horodaté dans le log"""
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def lire_state():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(l.strip() for l in f.readlines())


def ecrire_state(state_set):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        for item in state_set:
            f.write(item + "\n")


def deja_alerté(tag: str) -> bool:
    state = lire_state()
    return tag in state


def marquer_comme_alerté(tag: str):
    state = lire_state()
    state.add(tag)
    ecrire_state(state)


def envoyer_mail(sujet, contenu):
    """Envoie un mail via SendGrid"""
    if not SENDGRID_API_KEY:
        log_event("❌ Pas de clé SendGrid configurée")
        return

    data = {
        "personalizations": [{"to": [{"email": EMAIL_TO}]}],
        "from": {"email": EMAIL_SENDER},
        "subject": sujet,
        "content": [{"type": "text/plain", "value": contenu}],
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}",
                 "Content-Type": "application/json"},
        json=data
    )

    if response.status_code == 202:
        log_event("✅ Email envoyé avec succès !")
    else:
        log_event(f"❌ Erreur lors de l'envoi de l'email : {response.status_code} {response.text}")


# ========= SCRAPER =========
def extraire_texte(url):
    scraper = cloudscraper.create_scraper()
    try:
        r = scraper.get(url, timeout=30)
        r.raise_for_status()
        return r.text[:500]  # extrait seulement le début
    except Exception as e:
        log_event(f"❌ Erreur HTTP : {e}")
        return ""


# ========= MAIN =========
def main():
    if not URL:
        log_event("❌ Erreur : RDV_URL n'est pas défini dans les variables Railway")
        return

    texte = extraire_texte(URL)

    if "rendez-vous" in texte.lower():
        log_event("✅ Rendez-vous trouvé → envoi d'alerte")
        envoyer_mail("Rendez-vous disponible !", texte)
        marquer_comme_alerté("rdv")

    elif "just a moment" in texte.lower() or "enable javascript" in texte.lower():
        if not deja_alerté("cloudflare"):
            log_event("⚠️ Bloqué par Cloudflare → alerte envoyée")
            envoyer_mail("Bloqué par Cloudflare", texte)
            marquer_comme_alerté("cloudflare")
        else:
            log_event("⚠️ Bloqué par Cloudflare → déjà alerté, pas d'envoi")

    else:
        # Cas inattendu (site down, maintenance, etc.)
        if not deja_alerté("inattendu"):
            log_event("⚠️ Texte inattendu → alerte envoyée")
            envoyer_mail("Texte inattendu sur le site", texte)
            marquer_comme_alerté("inattendu")
        else:
            log_event("⚠️ Texte inattendu → déjà alerté, pas d'envoi")


if __name__ == "__main__":
    main()
