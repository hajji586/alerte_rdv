import os
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import cloudscraper
from datetime import datetime

# ========================
#  Fonction de logging
# ========================
def log(message: str):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    ligne = f"{timestamp} {message}"
    print(ligne)
    with open("alerte_rdv.log", "a", encoding="utf-8") as f:
        f.write(ligne + "\n")

# ========================
#  Récupération de la page
# ========================
def recuperer_page(url: str) -> str:
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        response = scraper.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as e:
        log(f"❌ Erreur HTTP : {e}")
        return ""

# ========================
#  Analyse du contenu HTML
# ========================
def analyser_page(html: str) -> str:
    # 1. Vérifier si un créneau au format HH:MM apparaît
    if re.search(r"\b\d{2}:\d{2}\b", html):
        return "RDV_DISPONIBLE"

    # 2. Cas Cloudflare / blocage JS
    if "Just a moment..." in html or "Enable JavaScript" in html:
        return "CLOUDFLARE"

    # 3. Cas standard "Pas de rendez-vous"
    if "Pas de rendez-vous disponible" in html:
        return "INDISPONIBLE"

    # 4. Sinon texte inattendu
    return "INCONNU"

# ========================
#  Envoi d'email
# ========================
def envoyer_mail(sujet: str, corps: str):
    try:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        destinataire = os.getenv("DESTINATAIRE")

        if not smtp_host or not smtp_user or not smtp_pass or not destinataire:
            log("❌ Erreur : variables SMTP manquantes dans Railway")
            return

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = destinataire
        msg["Subject"] = sujet
        msg.attach(MIMEText(corps, "plain", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        log("✅ Email envoyé avec succès !")

    except Exception as e:
        log(f"❌ Erreur lors de l'envoi de l'email : {e}")

# ========================
#  Programme principal
# ========================
def main():
    url = os.getenv("RDV_URL")
    if not url:
        log("❌ Erreur : RDV_URL n'est pas défini dans les variables Railway")
        return

    log("🔍 Vérification des rendez-vous...")
    html = recuperer_page(url)
    if not html:
        return

    etat = analyser_page(html)

    if etat == "RDV_DISPONIBLE":
        log("🚨 RDV disponible trouvé → envoi immédiat d'alerte")
        envoyer_mail("🚨 RDV DISPONIBLE !", "Un créneau est visible sur le site TLSContact.")
    elif etat == "CLOUDFLARE":
        log("⚠️ Bloqué par Cloudflare → pas d'envoi")
    elif etat == "INDISPONIBLE":
        log("❌ Aucun rendez-vous disponible")
    else:
        log("⚠️ Texte inattendu → pas d'envoi (déjà alerté si nécessaire)")

if __name__ == "__main__":
    main()
