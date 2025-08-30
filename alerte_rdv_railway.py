import os
import cloudscraper
import smtplib
from email.message import EmailMessage

# Variables d'environnement
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")

# URL à surveiller
URL_RDV = "https://visas-fr.tlscontact.com/22318807/workflow/appointment-booking?location=tnTUN2fr"

def verifier_rdv():
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL_RDV)
    texte = response.text
    return texte

def envoyer_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP("smtp.sendgrid.net", 587) as server:
            server.starttls()
            server.login("apikey", SENDGRID_API_KEY)
            server.send_message(msg)
        print("✅ Email envoyé !")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")

def main():
    texte = verifier_rdv()
    print("Texte RDV (extrait):", texte[:100])

    # Envoi d’un mail uniquement si un rendez-vous est disponible
    if "Aucun rendez-vous disponible" not in texte:
        sujet = "⚠️ Rendez-vous disponible trouvé !"
        corps = f"Texte RDV :\n{texte[:500]}"
        envoyer_email(sujet, corps)
    else:
        print("⏳ Pas de rendez-vous disponible. Aucune alerte envoyée.")

if __name__ == "__main__":
    main()
