# ⚡ DevDeck — Cockpit Développeur Tout-en-Un

DevDeck est un tableau de bord de travail et un gestionnaire de projets pour développeurs, **100% local, ultra-léger et respectueux de la vie privée**.

Il regroupe au même endroit tous vos projets locaux, vous permet de lancer vos serveurs de développement ou de production en un clic, d'afficher les logs en direct avec coloration ANSI, de résoudre les conflits de ports, d'éditer vos `.env`, de superviser Git/GitHub et de tester vos APIs sans quitter l'interface.

---

## 🌟 Fonctionnalités Clés

### 1. 🚀 Gestionnaire de Projets & Serveurs Locaux
- **Détection automatique de stack :** Détecte automatiquement Next.js, Vite, React, Vue, Express, Python (Django, FastAPI, Flask), Go, Rust, Docker Compose, etc.
- **Lancement en 1 clic :**
  - Mode **Dev** (ex: `npm run dev`)
  - Mode **Prod locale** (ex: `npm run build && npm run start` ou `python3 app.py`)
  - Mode **Tests** (ex: `npm test` ou `pytest`)
- **Supervision des processus :** Suivi en temps réel de l'état (🟢 En ligne avec PID, ⚪ Arrêté, 🔴 Erreur), du temps d'activité (uptime) et lien direct vers le port d'écoute (`http://localhost:3000`).
- **Raccourcis intégrés :** Ouvrir dans VS Code (`code .`), ouvrir dans le gestionnaire de fichiers (`xdg-open`).

### 2. 📟 Terminal & Logs en Direct (SSE)
- **Streaming temps réel :** Console intégrée avec rendu complet des couleurs ANSI, auto-scroll, redémarrage du serveur et copie dans le presse-papiers.
- **Buffer d'historique :** Conserve les 1000 dernières lignes de logs même si vous changez d'onglet.

### 3. 🔌 Inspecteur de Ports & Tueur de Conflits
- Liste tous les ports TCP en écoute sur votre machine (`3000`, `5173`, `8000`, `5432`...).
- **Résolution des conflits `EADDRINUSE` :** Bouton 1-clic pour libérer le port en envoyant un signal de terminaison propre (`SIGTERM` / `SIGKILL`).

### 4. 🌿 Git & GitHub Hub
- **Git en local :** Statut des fichiers modifiés, indexés (staged) et non suivis. Commits d'avance/retard sur le remote.
- **Actions rapides :** `git pull`, `git push`, `git fetch`, changement de branche en 1 clic, boîte de dialogue de commit.
- **GitHub :** Aperçu en direct des Pull Requests ouvertes, Issues et workflows GitHub Actions (CI/CD).

### 5. 🔐 Gestionnaire de Variables d'Environnement (`.env`)
- Éditeur visuel pour `.env`, `.env.local`, `.env.production`.
- Masquage des variables sensibles (clés API, mots de passe, tokens) avec bouton œil 👁️ pour afficher.
- **Comparateur intelligent :** Alerte en cas de variables manquantes par rapport à `.env.example`.
- Sauvegarde sécurisée avec copie automatique `.bak`.

### 6. 🐳 Services Docker
- Surveillance des conteneurs en cours et commandes Docker Compose (`up`, `down`, `restart`).

### 7. 🛠️ Boîte à outils Développeur (DevTools)
- **Client HTTP / REST :** Alternative légère à Postman pour tester vos endpoints locaux ou distants (GET/POST/PUT/DELETE, headers, body JSON, calcul du temps de réponse en ms).
- **Décodeur JWT :** Décode instantanément les en-têtes et le payload de jetons JWT avec conversion des dates d'expiration.
- **Générateur de clés :** Génération rapide d'UUIDs v4, clés secrètes hexadécimales et jetons d'authentification.

---

## 💻 Installation & Démarrage

### Prérequis
* **Python 3.10+** (inclus par défaut sur la plupart des systèmes Linux / macOS)
* Aucun `pip install` ni `npm install` requis pour le dashboard : **zéro dépendance externe lourde !**

### Installation en 1 ligne :

```bash
git clone https://github.com/votre-nom/devdeck.git
cd devdeck
./install.sh
```

Le script `install.sh` configure les permissions d'exécution et installe automatiquement le raccourci dans votre menu d'applications (`devdeck.desktop`).

### Lancer l'application :

```bash
./devdeck
```
Ou bien :
```bash
python3 app.py
```

L'application s'ouvre automatiquement dans votre navigateur à l'adresse :
👉 **http://127.0.0.1:8888**

---

## 🏗️ Structure du Projet

```
devdeck/
├── devdeck                  # Script de lancement exécutable
├── install.sh               # Script d'installation automatique
├── app.py                   # Serveur HTTP/SSE en Python pur standard
├── core/
│   ├── config.py            # Sauvegarde des projets et réglages (JSON)
│   ├── detector.py          # Détecteur automatique de stacks et commandes
│   ├── process_manager.py   # Gestionnaire de sous-processus et pseudo-terminaux (PTY)
│   ├── port_manager.py      # Scanner de ports et résolution de conflits
│   ├── git_manager.py       # Actions Git locales
│   ├── github_manager.py    # Intégration de l'API GitHub
│   ├── env_manager.py       # Analyse et édition des fichiers .env
│   ├── docker_manager.py    # Surveillance des conteneurs Docker
│   └── tools_manager.py     # Client HTTP, JWT, Hashes, UUID
├── web/
│   ├── index.html           # Interface utilisateur SPA
│   ├── css/devdeck.css      # Thème sombre moderne pour développeur
│   └── js/                  # Modules JavaScript frontend modulaires
└── data/                    # Données locales (exclues de Git via .gitignore)
```

---

## 🔒 Confidentialité & Sécurité

* Toutes vos données restent **strictement locales** sur votre machine (`127.0.0.1`).
* Vos fichiers de configuration (`data/projects.json`, `data/settings.json`, `.env`) sont systématiquement ignorés par `.gitignore` et ne seront jamais poussés sur GitHub.

---

## 📄 Licence

Ce projet est sous licence [MIT](LICENSE). Libre d'utilisation, de modification et de distribution.
