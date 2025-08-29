import os
import requests
from bs4 import BeautifulSoup
import smtplib

# --- Configuration SendGrid ---
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")

def send_email(subject, body):
    if not SENDGRID_API_KEY or not EMAIL_FROM or not EMAIL_TO:
        print("⚠️ Configuration email incomplète")
        return

    import urllib.request
    import json

    data = {
        "personalizations": [{"to": [{"email": EMAIL_TO}]}],
        "from": {"email": EMAIL_FROM},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print("✅ Email envoyé ! Status code :", resp.getcode())
    except Exception as e:
        print("❌ Erreur lors de l'envoi de l'email :", e)

def check_rdv():
    url = "https://visas-fr.tlscontact.com/22318807/workflow/appointment-booking?location=tnTUN2fr"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Récupération du texte RDV
    texte_rdv = soup.get_text(strip=True)
    print("Texte RDV (extrait):", texte_rdv[:200])

    if "Aucun rendez-vous disponible" in texte_rdv:
        print("ℹ️ Aucun rendez-vous dispo → pas d'alerte.")
    else:
        print("⚠️ Texte inattendu, envoi d'une alerte pour vérification manuelle")
        send_email(
            "⚠️ [ALERTE] Vérification manuelle requise",
            f"Le texte ne contient PAS 'Aucun rendez-vous disponible'.\n\nExtrait:\n{texte_rdv[:500]}"
        )

if __name__ == "__main__":
    check_rdv()
