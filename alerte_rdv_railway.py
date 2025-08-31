import cloudscraper
import os
import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Variables d'environnement
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_TO = os.getenv("MAIL_TO")
URL_RDV = os.getenv("URL_RDV")  # URL du site de RDV

# Fichier de log
LOG_FILE = "alerte_rdv.log"
LAST_CF_ALERT_FILE = "last_cf_alert.txt"

# Crée un scraper Cloudflare
scraper = cloudscraper.create_scraper()

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def send_email(subject, content):
    if not SENDGRID_API_KEY or not MAIL_FROM or not MAIL_TO:
        log_message("⚠️ Email non envoyé : variables d'environnement manquantes")
        return
    try:
        mail = Mail(from_email=MAIL_FROM, to_emails=MAIL_TO, subject=subject, plain_text_content=content)
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(mail)
        log_message(f"✅ Email envoyé ! Status code : {response.status_code}")
    except Exception as e:
        log_message(f"❌ Erreur lors de l'envoi de l'email : {e}")

def main():
    try:
        response = scraper.get(URL_RDV)
        texte_rdv = response.text[:200]  # extrait pour le log
    except Exception as e:
        log_message(f"❌ Erreur HTTP : {e}")
        return

    if "Just a moment..." in response.text or response.status_code == 503:
        # Détection Cloudflare
        last_alert = ""
        if os.path.exists(LAST_CF_ALERT_FILE):
            with open(LAST_CF_ALERT_FILE, "r", encoding="utf-8") as f:
                last_alert = f.read().strip()
        if last_alert != "cf":
            log_message(f"⚠️ Bloqué par Cloudflare → alerte envoyée")
            send_email("⚠️ Alerte Cloudflare", f"Page RDV bloquée par Cloudflare : {URL_RDV}")
            with open(LAST_CF_ALERT_FILE, "w", encoding="utf-8") as f:
                f.write("cf")
        else:
            log_message("⚠️ Bloqué par Cloudflare → déjà alerté, pas d'envoi")
        return

    # Réinitialiser le fichier Cloudflare si page OK
    if os.path.exists(LAST_CF_ALERT_FILE):
        os.remove(LAST_CF_ALERT_FILE)

    # Détection d'un vrai créneau
    if "Rendez-vous disponible" in response.text:
        log_message("Rendez-vous disponible → envoi email")
        send_email("Rendez-vous disponible", f"Un créneau est disponible : {URL_RDV}")
    else:
        log_message("Pas de créneau disponible, aucun email envoyé")

if __name__ == "__main__":
    main()

