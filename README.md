# 🚨 Alerte RDV Automatisée

Ce projet surveille automatiquement une page web (ex. prise de rendez-vous) et envoie un **email d’alerte** dès qu’un créneau est détecté.  
Déployé et exécuté toutes les 5 minutes via **Railway + Cron job**.

---

## ⚙️ Fonctionnalités
- Scraping avec **Cloudscraper** (bypass Cloudflare).
- Mode **silencieux** : n’envoie pas 50 fois la même alerte.
- **Logs horodatés** dans `alerte.log`.
- Déploiement **Railway** avec redéploiement automatique à chaque commit Git.
- Envoi d’email via **SendGrid SMTP**.

---

## 📂 Structure du projet
alerte_rdv/
├── alerte_rdv_railway.py # Script principal
├── requirements.txt # Dépendances Python
├── Procfile # Pour Railway
├── .gitignore # Ignore logs, cache, etc.
├── README.md # Documentation
└── alerte.log # Généré automatiquement (non versionné)