import os
import cloudscraper
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from loguru import logger

# ==============================
# Config
# ==============================
URL = "https://visas-fr.tlscontact.com/22318807/workflow/appointment-booking?location=tnTUN2fr"

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"

# ==============================
# Fonction d’envoi d’email
# ==============================
def send_email(subject, content):
    if not SENDGRID_API_KEY or not EMAIL_TO or not EMAIL_FROM:
        logger.error("❌ Configuration email manquante. Vérifie tes variables d'environnement.")
        return

    try:
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=subject,
            plain_text_content=content
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.success(f"✅ Email envoyé ! Status code : {response.status_code}")
    except Exception as e:
        logger.exception(f"❌ Erreur lors de l'envoi de l'email : {e}")

# ==============================
# Fonction de scraping
# ==============================
def check_rdv():
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(URL, timeout=20)
        text = response.text.strip()
        preview = text[:150].replace("\n", " ")

        logger.info(f"📄 Texte RDV (extrait): {preview}")

        if TEST_MODE:
            logger.warning("⚠️ Mode TEST activé → envoi email forcé")
            send_email("ALERTE TEST RDV", "Ceci est un test d'alerte.")
        elif "Aucun rendez-vous disponible" in text:
            logger.info("ℹ️ Aucun rendez-vous disponible pour le moment.")
        elif "Enable JavaScript and cookies" in text:
            logger.warning("⚠️ Challenge Cloudflare détecté → envoi alerte pour vérification")
            send_email("⚠️ Vérification nécessaire TLSContact", "Le site demande JavaScript/cookies (Cloudflare).")
        else:
            logger.success("🎉 Rendez-vous disponible détecté → envoi alerte")
            send_email("🎉 RDV disponible TLSContact", "Un rendez-vous est disponible, connecte-toi vite !")

    except Exception as e:
        logger.exception(f"❌ Erreur lors du scraping : {e}")

# ==============================
# Point d’entrée
# ==============================
if __name__ == "__main__":
    logger.info("🚀 Lancement du script de surveillance TLSContact")
    check_rdv()
