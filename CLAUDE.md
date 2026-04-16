# Whitehat Challenge A — Flask Secure Product App

> Document maître du projet. Lu automatiquement par Claude Code à chaque session.
> Mis à jour après chaque étape.

---

## 0. Énoncé du devoir

> ⚠️ À REMPLIR : coller ici le texte exact du mail de Yarden (passage Challenge A).
> Si le texte est en hébreu, conserver l'original ET ajouter une traduction française en dessous.

**Spécifications connues à ce jour :**
- App web avec 2 pages :
  - Page d'insertion de produits (champs : nom, prix)
  - Page de recherche de produits
- Connexion DB via requêtes SQL
- Une seule table contenant produits + prix
- Langage libre
- Critère principal : "que le système tourne". Sécurité = bonus apprécié.

---

## 1. Contexte du projet

App web minimale de gestion de produits (CRUD partiel : Create + Read).
Objectif pédagogique : démontrer une approche **secure-by-design** sur les vulnérabilités applicables.

**Cible recruteur :** White-Hat (filiale EPAM, cybersécurité Israël) — poste pentester / auditeur applicatif.
Le code doit pouvoir être défendu en entretien technique face à des pentesters senior.

---

## 2. Stack technique

| Composant | Version | Justification |
|---|---|---|
| Python | 3.14.4 | Latest stable (oct 2025). Choisi vs Python 3.9 système (EOL dépassée). Installé via Homebrew (`brew install python@3.14`). |
| Flask | 3.1.3 | Micro-framework, minimal, rien de caché. Facilite la démonstration explicite de chaque couche de sécurité. |
| SQLite | stdlib (`sqlite3`) | Aucune dépendance externe. Suffisant pour une seule table. Fichier unique = facile à déployer/auditer. |
| Jinja2 | 3.1.6 | Templating intégré à Flask. Auto-escape activé par défaut → première ligne de défense XSS. |
| Werkzeug | 3.1.8 | Serveur de dev WSGI sous Flask. |

**OS de dev :** macOS (Apple Silicon). Le code reste portable Linux/Windows.

---

## 3. Structure du projet

```
whitehat-challenge-a/
├── .git/                    # Repo git (init main)
├── .gitignore               # Exclusions (venv, *.db, __pycache__, .env)
├── venv/                    # Environnement virtuel Python (NON commité)
├── requirements.txt         # Dépendances figées (pip freeze)
├── CLAUDE.md                # Ce fichier
└── README.md                # Doc utilisateur (sera enrichi en étape 8)
```

(Sera complétée à chaque ajout de fichier.)

---

## 4. Plan d'exécution

| # | Étape | Statut |
|---|---|---|
| 1 | Setup environnement (venv, Flask, git) | ✅ FAIT |
| 2 | Schéma DB SQLite + script init | ⬜ À faire |
| 3 | App Flask minimale qui tourne | ⬜ À faire |
| 4 | Page insertion (volontairement vulnérable) | ⬜ À faire |
| 5 | Page recherche (volontairement vulnérable) | ⬜ À faire |
| 6 | Sécurisation des 6 vulnérabilités identifiées | ⬜ À faire |
| 7 | Tests croisés (avant/après par vuln) | ⬜ À faire |
| 8 | README final orienté recruteur | ⬜ À faire |
| 9 | Revue de simulation d'entretien | ⬜ À faire |

---

## 5. Décisions techniques (et leurs "pourquoi")

| Décision | Pourquoi |
|---|---|
| Python 3.14 plutôt que 3.9 système | Le 3.9 est EOL depuis oct 2025 → mauvaise image pour un poste sécurité. |
| Flask plutôt que Django | Django cache trop de choses (auto-CSRF, auto-ORM). Flask oblige à expliciter chaque protection → meilleure démonstration pédagogique. |
| SQLite plutôt que Postgres/MySQL | Une seule table, pas de besoin réseau, zéro setup. Permet de focaliser sur le SQL et la sécurité, pas l'infra. |
| Venv Python isolé | Reproductibilité : `requirements.txt` permet à n'importe qui de recréer l'env exact. |
| Approche "vulnérable d'abord, sécurisé ensuite" | Permet de voir les attaques marcher, puis de prouver que la protection les bloque. Argument fort en entretien. |
| Commits git en anglais | Convention pro standard. |
| Pas de déploiement Vercel | SQLite incompatible serverless (filesystem éphémère). Livraison = lien GitHub + run local. |

---

## 6. Vulnérabilités traitées

(Sera rempli à partir de l'étape 6.)

| # | Vuln | Statut | Méthode de protection | Payload de test |
|---|---|---|---|---|
| 1 | SQL Injection | ⬜ | — | — |
| 2 | XSS | ⬜ | — | — |
| 3 | CSRF | ⬜ | — | — |
| 4 | Clickjacking | ⬜ | — | — |
| 5 | Security Misconfiguration | ⬜ | — | — |
| 6 | Sensitive Data Exposure | ⬜ | — | — |

---

## 7. Commandes utiles

```bash
# Activer l'environnement virtuel (à faire à chaque nouvelle session terminal)
cd ~/whitehat-challenge-a
source venv/bin/activate

# Désactiver le venv
deactivate

# Réinstaller les dépendances depuis requirements.txt
pip install -r requirements.txt

# Vérifier la version de Flask et Python actives
python -c "import flask, sys; print(f'Flask {flask.__version__} on Python {sys.version.split()[0]}')"
```

(Lancement serveur, init DB, etc. seront ajoutés aux prochaines étapes.)

---

## 8. Préparation entretien — Questions probables et réponses

### Étape 1 (setup)

**Q : Pourquoi un environnement virtuel ?**
R : Pour isoler les dépendances du projet du Python système. Évite les conflits de versions entre projets et permet une reproductibilité parfaite via `requirements.txt`. Bonne pratique systématique en Python.

**Q : Pourquoi `pip freeze > requirements.txt` plutôt que d'écrire le fichier à la main ?**
R : `pip freeze` capture **toutes** les dépendances installées avec leurs versions exactes (ex : `Flask==3.1.3`), y compris les dépendances transitives (Jinja2, Werkzeug, etc.). Garantit que tout collaborateur aura exactement le même environnement.

**Q : Pourquoi exclure `venv/` du git ?**
R : Le venv contient des binaires Python compilés pour l'OS et l'architecture spécifiques de la machine de dev. Si quelqu'un clone le repo sur Linux, ces binaires ne fonctionnent pas. La pratique pro : commiter `requirements.txt` + chacun recrée son venv localement.

**Q : Pourquoi spécifier Python 3.14 et pas la version par défaut du système ?**
R : Le Python 3.9.6 fourni par macOS est en fin de vie depuis octobre 2025 (plus de patches de sécurité). Utiliser une version maintenue est un réflexe sécurité de base.

(Sera enrichi à chaque étape.)

---

## 9. Journal des incidents / corrections

(Vide pour l'instant. À remplir si quelque chose dévie du plan.)
