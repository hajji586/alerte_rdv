import os
import cloudscraper
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# -----------------------------
# Configuration depuis Railway
# -----------------------------
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"

# URL TLSContact
URL = "https://visas-fr.tlscontact.com/22318807/workflow/appointment-booking?location=tnTUN2fr"

# -----------------------------
# Fonction pour envoyer un mail
# -----------------------------
def send_email(subject, body):
    if not SENDGRID_API_KEY:
        print("❌ Pas de clé SendGrid configurée, impossible d’envoyer un mail.")
        return

    print("📧 Envoi de l'email...")

    data = {
        "personalizations": [{
            "to": [{"email": EMAIL_TO}],
            "subject": subject
        }],
        "from": {"email": EMAIL_FROM},
        "content": [{"type": "text/plain", "value": body}]
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json=data
    )

    if response.status_code == 202:
        print("✅ Email envoyé avec succès !")
    else:
        print(f"❌ Erreur lors de l’envoi : {response.status_code} → {response.text}")

# -----------------------------
# Vérification RDV
# -----------------------------
def check_rdv():
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'firefox',
            'platform': 'windows',
            'mobile': False
        }
    )

    try:
        response = scraper.get(URL, timeout=20)
        texte = response.text.strip()

        # Log partiel pour éviter le spam énorme
        print("Texte RDV (extrait):", texte[:200])

        # Mode test forcé
        if TEST_MODE:
            send_email("✅ TEST MODE : Alerte RDV", "Ceci est un email de test.")
            return

        # Vérification du contenu
        if "Aucun rendez-vous disponible" in texte:
            print("ℹ️ Aucun RDV disponible")
        elif "Just a moment" in texte or "Enable JavaScript" in texte:
            print("⚠️ Bloqué par Cloudflare → alerte envoyée")
            send_email("⚠️ Vérification manuelle requise",
                       "TLSContact a renvoyé une page de sécurité. Vérifie manuellement : " + URL)
        else:
            print("✅ RDV disponible ou texte inattendu → alerte envoyée")
            send_email("✅ RDV trouvé !",
                       "Un rendez-vous est peut-être disponible. Vérifie : " + URL)

    except Exception as e:
        print("❌ Erreur lors de la récupération :", str(e))
        send_email("❌ Erreur script RDV",
                   f"Le script a rencontré une erreur : {str(e)}")

# -----------------------------
# Exécution
# -----------------------------
if __name__ == "__main__":
    check_rdv()

# Redeploy test - 2025-08-30
