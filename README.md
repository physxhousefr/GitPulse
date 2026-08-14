<div align="center">

# ⚡ GitPulse — Bot Auto-Commit & Auto-Push

**Gestionnaire d'Auto-Push Git intelligent avec Interface Web Dark Glassmorphic & Icône System Tray (Windows)**

[![GitHub Repo](https://img.shields.io/badge/GitHub-physxhousefr%2FGitPulse-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/physxhousefr/GitPulse)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Backend-Flask_REST-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![UI](https://img.shields.io/badge/UI-Dark_Glassmorphism-00f2fe?style=for-the-badge&logo=css3&logoColor=white)](#-interface-graphique)
[![Platform](https://img.shields.io/badge/Platform-Windows_10_%2F_11-blue?style=for-the-badge&logo=windows11&logoColor=white)](https://microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)

<p align="center">
  <a href="#-vue-densemble">Vue d'Ensemble</a> •
  <a href="#-fonctionnalités-phares">Fonctionnalités</a> •
  <a href="#-structure-du-projet">Architecture</a> •
  <a href="#-installation--démarrage">Installation</a> •
  <a href="#-modes-dauto-commit">Modes de Commit</a> •
  <a href="#-faq--dépannage">FAQ & Dépannage</a> •
  <a href="#-licence">Licence</a>
</p>

---

</div>

## 🌟 Vue d'Ensemble

**GitPulse** est une application autonome moderne conçue pour automatiser la synchronisation (commit & push) de vos dépôts Git locaux vers vos dépôts distants (GitHub, GitLab, Gitea). 

Grâce à son interface Web réactive au style **Dark Glassmorphism**, sa console de logs en temps réel via SSE, son intégration native dans la barre des tâches Windows (**System Tray**) et son moteur d'auto-commit intelligent basé sur l'analyse de diff, GitPulse maintient votre profil et vos dépôts à jour sans jamais perturber votre travail.

---

## ✨ Fonctionnalités Phares

- **🎨 Interface Web Cyberpunk / Glassmorphism** :
  - Dashboard moderne avec verre dépoli (`backdrop-filter`), thèmes sombres néon, et indicateurs LED d'état d'exécution.
  - Stream de logs en temps réel via **Server-Sent Events (SSE)** avec préfixe d'état `[-] gitpulse : message`.

- **📌 Intégration Native System Tray (Zone de notification Windows)** :
  - Se loge silencieusement à côté de l'heure (^).
  - Menu contextuel interactif :
    - 🌐 *Ouvrir le Dashboard Web* (`http://127.0.0.1:5050`)
    - 🟢 / 🔴 *Activer / Mettre en Pause le Bot*
    - ⚡ *Forcer Commit & Push Tout*
    - ❌ *Quitter GitPulse*

- **🧠 Moteur d'Auto-Commit Intelligent (Analyse de Diff)** :
  - Détecte le type de fichiers modifiés pour générer des messages de commit propres et professionnels :
    - 📝 Modifications de documentation ➔ `docs(readme): update README.md documentation`
    - ✨ Code source (C++, C#, Python, JS...) ➔ `feat(core): update source logic (main.cpp)`
    - 🎨 UI & Styles ➔ `style(ui): adjust interface styling & layout`
    - 🔧 Fichiers de configuration ➔ `chore(config): update build settings`
  - Styles de messages configurables : **Conventionnelle Intelligente**, **Emoji Intelligente** (`✨ feat:...`), ou **Template Personnalisée**.

- **📊 Heatmap d'Activité GitHub Réelle (365 Jours)** :
  - Grille de contribution interactive basée sur l'historique réel des commits de vos dépôts Git.
  - Info-bulle interactive indiquant la date exacte et le volume de commits (`X commits le YYYY-MM-DD`).
  - Statistiques en direct du nombre de lignes ajoutées (`+`) et supprimées (`-`).

- **🤫 Exécution Totalement Silencieuse (`CREATE_NO_WINDOW`)** :
  - Exécution en arrière-plan sans aucune pop-up ni clignotement de fenêtre console grâce au drapeau système `subprocess.CREATE_NO_WINDOW`.

- **⏰ Planification Aléatoire & Anti-Détection** :
  - Système de jitter aléatoire configurable (ex: 5 à 25 min d'écart) pour simuler une activité de développement naturelle.

- **🔄 Intégration au Démarrage de Windows** :
  - Configuration automatique en 1 clic pour lancer le bot discrètement dès l'allumage du PC.

---

## 🛠️ Structure du Projet

```text
git_auto_push_bot/
├── main.py                  # Point d'entrée principal (Serveur Web Flask & System Tray)
├── setup_autostart.py       # Générateur de raccourci au démarrage de Windows (.lnk)
├── requirements.txt         # Liste des dépendances Python (Flask, Flask-Cors, pystray, Pillow)
├── config.example.json      # Template de configuration exemple
├── GitPulse.lnk             # Raccourci Windows de lancement silencieux sans console
├── LICENSE                  # Licence Open-Source MIT
├── README.md                # Documentation officielle du projet
│
├── core/                    # Package Back-end Python
│   ├── __init__.py
│   ├── config_manager.py    # Gestion de la persistance JSON
│   ├── git_manager.py       # Wrapper Git, détection de branche & générateur de diff
│   ├── scheduler.py         # Moteur de boucle d'arrière-plan & diffusion SSE
│   └── tray_manager.py      # Gestionnaire d'icône système Windows Tray
│
├── static/                  # Ressources statiques Frontend
│   ├── css/style.css        # Thème CSS Glassmorphism
│   ├── js/app.js            # Logique Web Client JS, SSE Logs, Heatmap
│   └── images/
│       └── tray_icon.png    # Icône de la barre des tâches
│
└── templates/               # Vues HTML
    └── index.html           # Interface Web Dashboard
```

---

## 🚀 Installation & Démarrage

### 1. Prérequis
- **Python 3.10 ou supérieur** (Testé avec succès sous Python 3.13 x64)
- **Git CLI** installé et configuré sur votre système Windows avec vos accès GitHub (SSH ou HTTPS Credential Manager).

### 2. Cloner le Dépôt
```bash
git clone https://github.com/physxhousefr/GitPulse.git
cd GitPulse
```

### 3. Installer les Dépendances
```bash
pip install -r requirements.txt
```

### 4. Démarrage de l'Application

- **Option A (Recommandée - Silencieux dans la barre des tâches)** :
  Double-cliquez sur `GitPulse.lnk` ou lancez le raccourci **GitPulse** créé sur votre Bureau.

- **Option B (Démarrage Automatique avec Windows)** :
  Exécutez une fois le script de configuration :
  ```bash
  python setup_autostart.py
  ```

- **Option C (Mode Console / Développeur)** :
  ```bash
  python main.py
  ```

L'interface Web s'ouvrira automatiquement sur : **`http://127.0.0.1:5050`**

---

## ⚙️ Modes d'Auto-Commit Disponibles

| Mode | Fonctionnement |
| :--- | :--- |
| **Hybride** *(Recommandé)* | Commite et pousse vos modifications de code s'il y en a. Si le dépôt est propre, génère une entrée horodatée dans `ACTIVITY.md` pour maintenir l'activité. |
| **Fichiers Modifiés** | Ne déclenche un commit & push **que si des modifications réelles de fichiers** sont détectées dans votre espace de travail. |
| **Journal d'Activité** | Met à jour uniquement le journal `ACTIVITY.md` sans toucher à vos fichiers de code source. |

---

## ❓ FAQ & Dépannage

<details>
<summary><b>Comment arrêter le bot s'il tourne en arrière-plan ?</b></summary>
Faites un clic droit sur l'icône GitPulse située dans la zone de notification Windows (à côté de l'heure ^) et cliquez sur <b>Quitter GitPulse</b>.
</details>

<details>
<summary><b>Mes identifiants Git/GitHub sont-ils sécurisés ?</b></summary>
Oui. GitPulse n'enregistre ni ne manipule vos mots de passe ou tokens. Il utilise directement l'exécutable local <code>git</code> de votre système, tirant parti de vos clés SSH existantes ou du <i>Windows Git Credential Manager</i>.
</details>

<details>
<summary><b>Est-ce que le bot affiche des fenêtres noires intempestives pendant que je travaille ?</b></summary>
Non. Toutes les opérations système sont exécutées avec le drapeau <code>CREATE_NO_WINDOW</code>, garantissant 0 clignotement de console à l'écran.
</details>

---

## 📄 Licence

Ce projet est distribué sous la licence **MIT**. Consulter le fichier [`LICENSE`](./LICENSE) pour plus de détails.

---

<div align="center">
  <sub>Développé avec ❤️ pour la communauté Open Source • <a href="https://github.com/physxhousefr/GitPulse">physxhousefr/GitPulse</a></sub>
</div>
