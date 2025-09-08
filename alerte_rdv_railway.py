import os
import cloudscraper
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# --- Configuration du logging ---
logging.basicConfig(
    filename="alerte_rdv.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# --- Variables d'environnement ---
RDV_URL = os.getenv("RDV_URL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAIL_TO = os.getenv("MAIL_TO")
MAIL_FROM = os.getenv("MAIL_FROM")

if not RDV_URL:
    print("❌ Erreur : RDV_URL n'est pas défini dans les variables Railway")
    exit(1)

# --- Headers simulant un vrai navigateur ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/127.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://web.visas-fr.tlscontact.com/",
    "Connection": "keep-alive",
}

# --- Option cookies (si besoin, à remplir après export navigateur) ---
COOKIES = {
    # "cookie_name": "cookie_value"
}

# --- Cloudsraper pour contourner Cloudflare ---
scraper = cloudscraper.create_scraper(browser={"custom": "chrome"}, delay=10)


def envoyer_mail(sujet, message):
    """Envoi d'un mail via SendGrid API"""
    try:
        import requests

        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": MAIL_TO}]}],
                "from": {"email": MAIL_FROM},
                "subject": sujet,
                "content": [{"type": "text/plain", "value": message}],
            },
        )

        if resp.status_code == 202:
            print("✅ Email envoyé avec succès !")
            logging.info("Email envoyé : %s", sujet)
        else:
            print(f"❌ Erreur lors de l'envoi : {resp.status_code} {resp.text}")
            logging.error("Erreur envoi email : %s %s", resp.status_code, resp.text)
    except Exception as e:
        print(f"❌ Exception envoi email : {e}")
        logging.exception("Exception envoi email")


def verifier_rdv():
    print("[🔍] Vérification des rendez-vous...")
    try:
        response = scraper.get(RDV_URL, headers=HEADERS, cookies=COOKIES, timeout=30)
        response.raise_for_status()
        texte = response.text[:500]

        print(f"[...] Extrait reçu : {texte[:120]}")

        if "Notre site web est temporairement indisponible" in texte:
            envoyer_mail("⚠️ TLSContact indisponible", "Le site affiche une erreur.")
        elif "Aucun rendez-vous disponible" in texte:
            print("⏳ Aucun rendez-vous disponible")
        elif "Rendez-vous disponible" in texte:
            envoyer_mail("✅ Rendez-vous trouvé", "Un créneau est disponible !")
        else:
            envoyer_mail("⚠️ Texte inattendu", "Contenu différent détecté, vérifie manuellement.")
    except Exception as e:
        print(f"❌ Erreur HTTP : {e}")
        logging.exception("Erreur HTTP")


if __name__ == "__main__":
    verifier_rdv()
