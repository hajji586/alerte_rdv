import os
import requests
from bs4 import BeautifulSoup
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- Récupération des variables d'environnement ---
RDV_URL = os.environ.get("RDV_URL")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
TEST_EMAIL_ALERT = os.environ.get("TEST_EMAIL_ALERT", "false").lower() == "true"

# --- Vérification de la page de rendez-vous ---
response = requests.get(RDV_URL)
soup = BeautifulSoup(response.text, "html.parser")

# Exemple : récupérer le texte exact de la balise qui indique "Aucun rendez-vous disponible"
message_rdv = soup.select_one("#main > div:nth-child(1) > div > div:nth-child(2) > div:nth-child(2) > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div > p")
texte_rdv = message_rdv.get_text(strip=True) if message_rdv else ""

# --- Log pour debug ---
print("Texte RDV :", texte_rdv)

# --- Si nouveau rendez-vous disponible ou mode test ---
if "Aucun rendez-vous disponible" not in texte_rdv or TEST_EMAIL_ALERT:
    print("Rendez-vous disponible ou mode test activé → envoi email")
    try:
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject='⚠️ Nouvelle disponibilité de RDV',
            plain_text_content=f'Un nouveau créneau est disponible sur le site : {RDV_URL}'
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print("Email envoyé ! Status code :", response.status_code)
    except Exception as e:
        print("Erreur lors de l'envoi de l'email :", e)
else:
    print("Aucun rendez-vous disponible pour l'instant.")

