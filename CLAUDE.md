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
├── CLAUDE.md                # Document maître du projet
├── README.md                # Doc utilisateur (enrichi en étape 8)
├── cross-tests.md           # Résultats des tests croisés avant/après (étape 7)
├── interview-prep.md        # Fiche de révision Q&R pour l'entretien
├── security-audit.md        # Mapping code ↔ référentiel White-Hat (en anglais)
├── schema.sql               # Schéma SQL pur (table products + index)
├── init_db.py               # Script Python qui exécute schema.sql
├── app.py                   # App Flask (routes /, /insert)
├── static/                  # Fichiers statiques servis par Flask
│   └── style.css            # Styles globaux de l'app
├── templates/               # Templates Jinja2
│   ├── base.html            # Layout commun (header, nav, footer)
│   ├── home.html            # Page d'accueil
│   ├── insert.html          # Formulaire d'insertion (vulnérable)
│   └── search.html          # Page de recherche (vulnérable — XSS via | safe)
└── database.db              # Base SQLite générée (NON commitée)
```

---

## 4. Plan d'exécution

| # | Étape | Statut |
|---|---|---|
| 1 | Setup environnement (venv, Flask, git) | ✅ FAIT |
| 2 | Schéma DB SQLite + script init | ✅ FAIT |
| 3 | App Flask minimale qui tourne | ✅ FAIT |
| 4 | Page insertion (volontairement vulnérable) | ✅ FAIT (4 vulns démontrées) |
| 5 | Page recherche (volontairement vulnérable) | ✅ FAIT (XSS live + SQLi UNION) |
| 6 | Sécurisation des 6 vulnérabilités identifiées | ✅ FAIT (4 commits séparés) |
| 7 | Tests croisés (avant/après par vuln) | ✅ FAIT (cross-tests.md — 8/8 tests pass) |
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
| Prix stocké en `INTEGER` (centimes) | Évite les erreurs d'arrondi des floats (ex : `0.1+0.2≠0.3`). Standard bancaire. |
| `CHECK` constraints en DB | Defense in depth : si la validation Flask est bypassée, la DB elle-même rejette les données invalides (prix négatif, nom vide, nom > 200 chars). |
| `created_at DEFAULT CURRENT_TIMESTAMP` | Audit trail : permet de tracer quand un produit a été inséré (utile en cas d'incident). |
| Schéma SQL séparé du code Python (`schema.sql` + `init_db.py`) | Lisibilité, auditabilité par un DBA, séparation des préoccupations. |
| Index sur `name` | Performance des recherches en étape 5 (la table de prod peut grossir). |
| `AUTOINCREMENT` sur l'id | IDs jamais réutilisés → traçabilité des logs préservée même après suppression. |
| Port 5001 (pas 5000) | Le port 5000 est occupé par AirPlay Receiver depuis macOS Monterey → conflit silencieux. |
| `host=127.0.0.1` (pas `0.0.0.0`) | Bind localhost uniquement. Le serveur n'est pas exposé sur le réseau pendant le dev. |
| `debug=True` en dev (à fixer en étape 6 pour prod) | Auto-reload + page debug interactive. ⚠️ Werkzeug debugger permet l'exécution de code arbitraire si exposé : strictement DEV ONLY. |
| `python app.py` plutôt que `flask run` | Toute la config est explicite dans le code (host, port, debug). Facilite la défense en entretien et l'onboarding. |

---

## 6. Vulnérabilités traitées

(Sera rempli à partir de l'étape 6.)

| # | Vuln | Statut | Méthode de protection | Payload de test |
|---|---|---|---|---|
| 1 | SQL Injection | ✅ PATCHÉE (commit 4efd292) | `execute("... VALUES (?, ?)", (name, price))` — driver gère l'escaping | Plus de concaténation, plus de `executescript()` |
| 2 | XSS (stocké) | ✅ PATCHÉE (commit 0ad0694) | Suppression `\| safe` + validation whitelist Flask | `<img>` s'affiche comme `&lt;img&gt;` — inoffensif |
| 3 | CSRF | ✅ PATCHÉE (commit 067ca33) | Flask-WTF CSRFProtect + token caché dans le form | POST sans token → HTTP 400 |
| 4 | Clickjacking | ✅ PATCHÉE (commit 39988d7) | `X-Frame-Options: DENY` via after_request | Aucun iframe possible |
| 5 | Security Misconfiguration | ✅ PATCHÉE (commit 39988d7) | `debug` depuis env, CSP, Server header masqué | `FLASK_ENV=production` → debug=False |
| 6 | Sensitive Data Exposure | ✅ PATCHÉE (commit 39988d7) | Messages génériques client + logging serveur | Plus de détails DB dans les réponses HTTP |

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

# Initialiser (ou ré-initialiser) la base de données depuis schema.sql
python init_db.py

# Inspecter la DB depuis la CLI
python -c "import sqlite3; c=sqlite3.connect('database.db'); [print(r) for r in c.execute('PRAGMA table_info(products)')]"

# Compter les produits en base
python -c "import sqlite3; c=sqlite3.connect('database.db'); print(c.execute('SELECT COUNT(*) FROM products').fetchone()[0])"

# Lancer le serveur Flask (dev) sur http://127.0.0.1:5001
python app.py
# Arrêter avec Ctrl+C

# Tester l'endpoint en CLI (sans navigateur)
curl -i http://127.0.0.1:5001/
```

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

### Étape 2 (DB schema)

**Q : Pourquoi stocker le prix en INTEGER (centimes) plutôt qu'en REAL/FLOAT ?**
R : Les nombres flottants ont des erreurs d'arrondi (`0.1 + 0.2 = 0.30000000000000004` en IEEE 754). En finance ou e-commerce, c'est inacceptable. Le standard bancaire est de stocker en plus petite unité monétaire (centimes) en INTEGER, puis convertir à l'affichage.

**Q : Tu valides déjà les inputs côté Flask, pourquoi mettre AUSSI des CHECK constraints en DB ?**
R : Defense in depth. Si un jour Flask est bypassé (bug dans la validation, autre app qui tape directement la DB, injection partielle), la DB elle-même refuse les données invalides. C'est la dernière ligne de défense. J'ai testé : tentatives d'INSERT avec prix négatif, nom vide, nom > 200 chars, name NULL → toutes bloquées par la DB.

**Q : Pourquoi `executescript()` plutôt que `execute()` dans `init_db.py` ?**
R : `execute()` ne permet qu'une seule requête SQL à la fois. `executescript()` accepte un script multi-requêtes (CREATE TABLE + CREATE INDEX dans le même fichier). C'est exactement ce qu'on a dans `schema.sql`.

**Q : Pourquoi `with sqlite3.connect(...) as conn:` ?**
R : Context manager. Garantit que la connexion est fermée proprement même si une exception est levée pendant le bloc. Évite les fuites de ressources (file descriptors, locks DB).

**Q : Pourquoi `CREATE TABLE IF NOT EXISTS` plutôt que juste `CREATE TABLE` ?**
R : Idempotence. Le script peut être lancé plusieurs fois sans erreur. Utile en dev (re-run après modif), critique en prod (migrations).

**Q : Pourquoi un index sur `name` ?**
R : La page de recherche (étape 5) va faire des `WHERE name LIKE ...`. Sans index, c'est un full table scan O(n). Avec index, c'est O(log n). Sur une table à 100 000 produits, c'est la différence entre 500ms et 2ms.

**Q : Pourquoi `AUTOINCREMENT` plutôt que juste `INTEGER PRIMARY KEY` ?**
R : Sans AUTOINCREMENT, SQLite peut réutiliser un id supprimé. Si l'id 42 référençait le produit "Laptop", qu'on le supprime, et qu'un nouveau produit "Souris" prend l'id 42, tous mes anciens logs mentionnant "produit 42 = Laptop" deviennent trompeurs. AUTOINCREMENT garantit que les ids ne sont jamais réutilisés → traçabilité préservée.

### Étape 3 (Flask app)

**Q : Pourquoi port 5001 et pas 5000 ?**
R : Sur macOS depuis Monterey, AirPlay Receiver écoute sur le port 5000 par défaut. Si on lance Flask sur 5000, il y a conflit silencieux : soit Flask refuse de démarrer (port pris), soit pire, certaines requêtes peuvent atterrir sur AirPlay. C'est un cas concret de Security Misconfiguration → on utilise 5001 pour être safe.

**Q : Pourquoi `host="127.0.0.1"` plutôt que `"0.0.0.0"` ?**
R : `127.0.0.1` (loopback) bind le serveur uniquement à la machine locale. Personne sur le réseau (WiFi, LAN) ne peut y accéder. `0.0.0.0` bind toutes les interfaces → exposition réseau. En dev avec `debug=True`, exposer sur 0.0.0.0 ouvrirait le Werkzeug debugger à n'importe qui sur le WiFi → exécution de code arbitraire à distance. C'est un piège classique.

**Q : Pourquoi `debug=True` est dangereux en prod ?**
R : Le mode debug active le **Werkzeug interactive debugger**. En cas d'exception, il affiche une page web avec une console Python interactive. Si exposée à Internet, n'importe qui peut **exécuter du code Python arbitraire sur le serveur** depuis son navigateur (avec un PIN qu'on peut casser). C'est une RCE pré-authentifiée. Strictement DEV ONLY. → On le force à False en étape 6.

**Q : Tu as testé ton app, qu'est-ce que tu as vu de problématique dans la réponse HTTP ?**
R : Le header `Server: Werkzeug/3.1.8 Python/3.14.4` révèle ma stack et mes versions. Information Disclosure (CWE-200). Un attaquant peut chercher des CVE spécifiques à ces versions. → Sera fixé en étape 6 (Sensitive Data Exposure).

**Q : Pourquoi `python app.py` plutôt que `flask run` ?**
R : Avec `python app.py`, toute la config (host, port, debug) est explicite dans le code Python. `flask run` cache la config dans des variables d'environnement (`FLASK_APP`, `FLASK_DEBUG`, etc.) → moins lisible, plus de "magie". Pour un projet pédagogique destiné à être audité, l'explicite gagne.

### Étape 4 (page insertion vulnérable)

**Q : Pourquoi tu as introduit du code volontairement vulnérable ?**
R : Pour pouvoir prouver, en étape 6, que ma protection fonctionne réellement. La démarche : (1) j'écris la version vulnérable, (2) je joue l'attaque, (3) je montre qu'elle marche, (4) j'écris la version sécurisée, (5) je rejoue la même attaque, (6) je montre qu'elle échoue maintenant. C'est ça la **preuve concrète**, pas juste de l'incantation.

**Q : Tu as utilisé `executescript()` au lieu de `execute()` — c'est exprès ?**
R : Oui, et c'est important. `execute()` n'autorise qu'une seule instruction SQL → impossible d'enchaîner un `INSERT; DROP TABLE;`. `executescript()` autorise le multi-statement → la SQLi devient catastrophique (DROP TABLE possible). J'ai voulu reproduire le **pire cas réaliste** d'une SQLi pour que la démo soit éclatante.

**Q : Quel payload SQLi as-tu démontré ?**
R : `name=Hack', 0); DROP TABLE products; --`. La SQL construite devient : `INSERT INTO products (name, price) VALUES ('Hack', 0); DROP TABLE products; --', 0)`. Le `'` ferme la string SQL, le `;` enchaîne, le `DROP TABLE` détruit la table, le `--` commente la fin. Résultat : table products effacée.

**Q : Et l'XSS ?**
R : J'ai stocké `<img src=x onerror=alert(1)>` comme nom de produit. La DB le stocke verbatim (juste du texte 30 chars, conforme à toutes les contraintes). Quand on l'affichera (étape 5), si on n'échappe pas, le navigateur exécutera le JS. C'est de la **stored XSS** — la pire variante car elle persiste pour tous les visiteurs.

**Q : Pourquoi les CHECK constraints DB n'ont pas bloqué l'XSS ?**
R : Parce qu'XSS et SQLi sont des attaques **différentes**. CHECK constraints valident la **structure** des données (longueur, signe, valeurs autorisées). Elles ne savent pas ce qu'est du HTML/JS. Une couche de défense ne couvre qu'un type d'attaque — c'est pour ça qu'on combine plusieurs couches.

**Q : Pourquoi pas de CSRF token sur ton formulaire d'insertion ?**
R : C'est délibéré pour démontrer la vuln. Sans token, n'importe quel site externe peut héberger un formulaire qui POST vers mon `/insert`. Si un utilisateur visite ce site malveillant pendant qu'il est connecté chez moi (même sans clic, possible via auto-submit), un produit s'insère sans son consentement. Sera fixé étape 6 avec Flask-WTF.

**Q : Le message d'erreur DB est renvoyé brut au client. Pourquoi c'est grave ?**
R : Sensitive Data Exposure (CWE-209). Un message du genre `CHECK constraint failed: price >= 0` ou `no such table: products` révèle ma structure DB et mes contraintes à l'attaquant. Il peut affiner ses payloads. Bonne pratique : message générique côté client (`"An error occurred"`), détails dans les logs serveur.

### Étape 5 (page de recherche vulnérable)

**Q : Pourquoi l'XSS se déclenche sur la page de recherche et pas sur la page d'insertion ?**
R : L'XSS stocké ne se déclenche que quand le payload est **affiché** dans le navigateur. La page d'insertion reçoit le nom et le stocke en DB sans le réafficher (juste un redirect). La page de recherche lit le nom depuis la DB et l'injecte dans le HTML avec `| safe` — c'est là que le navigateur exécute le JS.

**Q : C'est quoi `| safe` dans Jinja2 et pourquoi c'est dangereux ?**
R : `| safe` est un filtre Jinja2 qui marque une valeur comme "HTML de confiance" et désactive l'auto-escape. Normalement `{{ "<script>" }}` devient `&lt;script&gt;` (inoffensif). Avec `{{ "<script>" | safe }}`, c'est injecté tel quel dans le HTML → le navigateur l'exécute. Le fix en étape 6 : supprimer `| safe`. Jinja2 auto-escape fait le reste.

**Q : Décris l'attaque UNION SELECT que tu as démontrée.**
R : Payload : `x' UNION SELECT 1,'HACKED BY ATTACKER',0,'2026-01-01'--`. La requête construite devient `SELECT id, name, price, created_at FROM products WHERE name LIKE '%x' UNION SELECT 1,'HACKED BY ATTACKER',0,'2026-01-01'--%'`. Le premier SELECT ne retourne rien (pas de 'x'), le UNION injecte une ligne forgée. En prod avec une table `users`, le payload serait `x' UNION SELECT 1,password,0,email FROM users--` → tous les mots de passe dans les résultats.

**Q : Décris l'attaque OR 1=1.**
R : Payload : `' OR '1'='1`. La requête devient `SELECT ... WHERE name LIKE '%' OR '1'='1%'`. La condition `'1'='1'` est toujours vraie → retourne TOUS les produits quelle que soit la recherche. Classique pour bypasser des filtres ou révéler tous les enregistrements d'une table.

### Étape 6 (sécurisation)

**Q : Comment as-tu fixé la SQL Injection ?**
R : Parameterized queries — `conn.execute('INSERT INTO products (name, price) VALUES (?, ?)', (name, price))`. Le driver SQLite3 passe les valeurs comme paramètres, jamais dans le texte SQL. Suppression de `executescript()` qui permettait le multi-statement. Payload `DROP TABLE` est maintenant traité comme une string littérale inoffensive.

**Q : Comment as-tu fixé le XSS stocké ?**
R : Deux actions combinées : (1) supprimé `| safe` dans `search.html` — Jinja2 auto-escape convertit `<img onerror=...>` en `&lt;img onerror=...&gt;`. (2) Ajouté `validate_name()` Flask qui rejette les inputs invalides côté serveur avant tout contact avec la DB.

**Q : Comment as-tu fixé le CSRF ?**
R : Flask-WTF `CSRFProtect(app)`. Token signé avec HMAC (via SECRET_KEY), inséré dans le formulaire `{{ csrf_token() }}`, validé à chaque POST. Un site externe ne peut pas lire ce token (same-origin policy) → son POST forgé reçoit HTTP 400 avant d'atteindre la logique SQL.

**Q : Comment as-tu masqué le header Server ?**
R : Double fix nécessaire : (1) `WSGIRequestHandler.server_version = 'Web Server'` + `version_string = lambda self: 'Web Server'` pour Werkzeug au niveau TCP. (2) `response.headers['Server'] = 'Web Server'` dans `@after_request` pour les responses Flask. En prod, c'est nginx qui gère ça avec `server_tokens off;`.

**Q : Comment as-tu géré les messages d'erreur verbeux ?**
R : `try/except sqlite3.Error` dans les deux routes — le message réel est logué côté serveur (`logger.error()`), le client reçoit un message générique. Des `@app.errorhandler(400/404/500)` personnalisés rendent `error.html` sans stack trace ni détail DB.

**Q : C'est quoi ta démarche globale pour la sécurisation ?**
R : 4 commits atomiques, un par vuln, avec messages conventionnels `security(sqli)`, `security(xss)`, `security(csrf)`, `security(headers)`. Chaque fix a été vérifié en rejouant l'attaque originale — si elle échoue, la protection est confirmée. J'ai aussi ajouté des couches beyond-the-spec : CSP header, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, et le debug contrôlé par env var.

---

## 9. Journal des incidents / corrections

(Vide pour l'instant. À remplir si quelque chose dévie du plan.)
