import cloudscraper
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from loguru import logger
import os

# -----------------------
# CONFIGURATION
# -----------------------
MODE_TEST = True  # Mettre False pour ne pas envoyer d'emails de test
URL_RDV = "https://visas-fr.tlscontact.com/22318807/workflow/appointment-booking?location=tnTUN2fr"
EMAIL_FROM = os.getenv("EMAIL_FROM")  # Ton email expéditeur
EMAIL_TO = os.getenv("EMAIL_TO")      # Ton email destinataire
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Clé SendGrid
# -----------------------

scraper = cloudscraper.create_scraper()

def get_texte_rdv():
    try:
        response = scraper.get(URL_RDV)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la page : {e}")
        return ""

def send_email(subject="Alerte RDV", content="Un nouveau rendez-vous est disponible !"):
    if not SENDGRID_API_KEY or not EMAIL_FROM or not EMAIL_TO:
        logger.error("Variables d'environnement pour l'email non définies")
        return
    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=EMAIL_TO,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.success(f"Email envoyé ! Status code : {response.status_code}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email : {e}")

def main():
    texte_rdv = get_texte_rdv()
    logger.info(f"Texte RDV (extrait): {texte_rdv[:100]}...")

    if "Rendez-vous disponible" in texte_rdv or MODE_TEST:
        logger.info("Rendez-vous disponible ou mode test activé → envoi email")
        send_email()
    else:
        logger.info("Aucun rendez-vous détecté → pas d'email envoyé")

if __name__ == "__main__":
    main()
