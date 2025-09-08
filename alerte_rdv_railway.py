import os
import cloudscraper
import logging
from datetime import datetime
import requests

# ---------------------
# Configuration logging
# ---------------------
LOG_FILE = "alerte.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ---------------------
# Variables d'environnement
# ---------------------
RDV_URL = os.getenv("RDV_URL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

if not RDV_URL or not SENDGRID_API_KEY or not ALERT_EMAIL:
    logging.error("❌ Variables d'environnement manquantes (RDV_URL, SENDGRID_API_KEY, ALERT_EMAIL)")
    exit(1)

# ---------------------
# Config cookies + User-Agent
# ---------------------
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/128.0.0.0 Safari/537.36"
}

# Si besoin, tu peux ajouter tes cookies ici :
cookies = {
    # "cookie_name": "cookie_value",
}

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

# ---------------------
# Fonction envoi d’email
# ---------------------
def envoyer_mail(sujet, contenu):
    url = "https://api.sendgrid.com/v3/mail/send"
    data = {
        "personalizations": [{
            "to": [{"email": ALERT_EMAIL}],
            "subject": sujet
        }],
        "from": {"email": ALERT_EMAIL},
        "content": [{"type": "text/plain", "value": contenu}]
    }
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}",
                 "Content-Type": "application/json"},
        json=data
    )
    if response.status_code == 202:
        logging.info(f"📧 Email envoyé : {sujet}")
    else:
        logging.error(f"❌ Erreur envoi email : {response.status_code} {response.text}")

# ---------------------
# Vérification RDV
# ---------------------
def verifier_rdv():
    logging.info("[🔍] Vérification des rendez-vous...")

    try:
        response = scraper.get(RDV_URL, headers=headers, cookies=cookies, timeout=30)
        response.raise_for_status()
        texte = response.text[:500]  # extrait pour debug

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur HTTP : {e}")
        return

    # Vérifier contenu
    if "Aucun rendez-vous disponible" in texte:
        logging.info("⏳ Aucun rendez-vous disponible.")
    elif "momentanément indisponible" in texte or "temporarily unavailable" in texte:
        logging.warning("⚠️ Site temporairement indisponible → envoi alerte")
        envoyer_mail("⚠️ TLSContact indisponible", texte[:200])
    else:
        logging.warning("✅ Rendez-vous possiblement dispo → envoi alerte")
        envoyer_mail("✅ Rendez-vous disponible !", texte[:500])

# ---------------------
# Exécution principale
# ---------------------
if __name__ == "__main__":
    verifier_rdv()
