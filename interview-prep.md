# Interview Prep — Questions & Réponses à mémoriser

> Fiche de révision pour l'entretien White-Hat / EPAM.
> Mise à jour à chaque étape du projet.
>
> **Comment l'utiliser :** lis la question, formule ta réponse à voix haute, vérifie avec la réponse modèle. Le but est de pouvoir **reformuler avec tes propres mots**, pas de réciter.

---

## 📚 Légende

- 🟢 **Réponse minimale** = ce qu'il faut au moins dire
- 🔵 **Pour aller plus loin** = bonus pour différencier ton profil
- ⚠️ **Piège** = formulation à éviter / erreur classique

---

# ÉTAPE 1 — Setup environnement Python

## Q1.1 — Pourquoi un environnement virtuel (venv) ?

🟢 **Réponse minimale :**
"Pour isoler les dépendances de ce projet du Python système et des autres projets. Évite les conflits de versions et garantit la reproductibilité."

🔵 **Pour aller plus loin :**
"Sans venv, si je travaille sur 2 projets qui ont besoin de Flask 2.x et Flask 3.x respectivement, j'ai un conflit. Avec venv, chaque projet a son propre dossier `venv/` contenant son interpréteur et ses libs."

⚠️ **Piège :** ne dis pas "pour la sécurité" — un venv ne sécurise pas, il **isole**.

---

## Q1.2 — Pourquoi `pip freeze > requirements.txt` ?

🟢 **Réponse minimale :**
"Pour figer les versions exactes de toutes les dépendances installées (y compris les transitives), afin que n'importe qui puisse recréer mon environnement à l'identique."

🔵 **Pour aller plus loin :**
"`pip freeze` capture les versions résolues à un instant T. C'est différent d'un `requirements.in` à la main qui ne listerait que mes dépendances directes. Pour la reproductibilité **stricte** avec hashes (anti supply-chain attack), on utiliserait `pip-compile` ou `uv` avec un lockfile."

---

## Q1.3 — Pourquoi `venv/` est dans le `.gitignore` ?

🟢 **Réponse minimale (3 raisons) :**
1. **Non-portable** : binaires compilés pour mon OS et mon architecture (macOS ARM64).
2. **Lourd** : 100-300 Mo de bruit dans le repo.
3. **Redondant** : `requirements.txt` permet de tout reconstruire.

🔵 **Pour aller plus loin :**
"Pour une reproductibilité maximale, on irait jusqu'au lockfile avec hashes SHA256 (`pip install --require-hashes`) pour bloquer une attaque supply-chain où un paquet PyPI compromis remplacerait la version 3.1.3 de Flask par une version malveillante portant le même numéro."

---

## Q1.4 — Pourquoi Python 3.14 plutôt que le 3.9.6 du système ?

🟢 **Réponse minimale (2 raisons) :**
1. **Sécurité** : Python 3.9 est en fin de vie (EOL) depuis octobre 2025 → plus de patches de sécurité. Incohérent pour un projet secure-by-design.
2. **Hygiène** : on ne touche jamais au Python système (utilisé par macOS lui-même). On installe une version dédiée via Homebrew ou pyenv.

🔵 **Pour aller plus loin :**
"La page officielle [devguide.python.org/versions](https://devguide.python.org/versions/) liste les statuts EOL. Pour un poste sécurité, utiliser une version EOL serait un red flag immédiat sur le CV."

---

## Q1.5 — Comment reconstruire l'environnement sur une autre machine ?

🟢 **Réponse minimale (4 commandes) :**
```bash
git clone <url>
cd whitehat-challenge-a
python3.14 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

🔵 **Pour aller plus loin :**
"Cette boucle `clone → venv → activate → install -r` est la signature du workflow Python pro. Si Python 3.14 n'est pas installé sur la nouvelle machine, on l'installe d'abord via `brew install python@3.14` (macOS) ou via `pyenv install 3.14`."

---

## Q1.6 — Pourquoi Flask plutôt que Django ?

🟢 **Réponse minimale :**
"Pour ce scope (2 pages, 1 table), Django serait surdimensionné. Flask est un micro-framework qui ne cache rien : chaque protection de sécurité est explicite dans mon code → meilleure démonstration de ma compréhension."

🔵 **Pour aller plus loin :**
"Django offre des protections automatiques (CSRF middleware actif par défaut, ORM qui paramétrise les requêtes). C'est une bonne chose en prod, mais pédagogiquement ça masque ce qui se passe vraiment. Avec Flask, j'ai dû activer chaque couche manuellement → je peux expliquer chaque ligne."

---

## Q1.7 — Pourquoi SQLite plutôt que PostgreSQL ou MySQL ?

🟢 **Réponse minimale :**
"Une seule table, aucun besoin de concurrence réseau, et SQLite est dans la stdlib Python. Zéro dépendance externe, fichier unique, parfait pour ce scope."

⚠️ **Piège :** ne dis pas "SQLite est moins sécurisé". C'est faux — SQLite est aussi sécurisé que les autres face aux injections SQL si on utilise des paramètres. La différence est l'usage (mono-utilisateur vs multi-utilisateurs concurrents).

🔵 **Pour aller plus loin :**
"En prod, SQLite n'est pas adapté au multi-write concurrent à grande échelle, et il est incompatible avec les architectures serverless (filesystem éphémère). Pour ce projet, c'était le bon choix. En prod sur Vercel, on serait passés à Vercel Postgres ou Turso."

---

# ÉTAPE 2 — Schéma DB SQLite

## Q2.1 — Pourquoi stocker le prix en INTEGER (centimes) plutôt qu'en REAL ?

🟢 **Réponse minimale :**
"Pour éviter les erreurs d'arrondi des floats. En IEEE 754, `0.1 + 0.2 = 0.30000000000000004`. En finance, c'est inacceptable. Le standard est de stocker en centimes (INTEGER), puis diviser par 100 à l'affichage."

🔵 **Pour aller plus loin :**
"C'est ce que font toutes les banques et processeurs de paiement (Stripe, PayPal). Une variante encore plus stricte est `DECIMAL(10,2)` en Postgres ou `Decimal` en Python — mais SQLite n'a pas de type DECIMAL natif, donc INTEGER en centimes est l'idiome SQLite."

⚠️ **Piège :** ne dis pas "REAL est moins précis" sans expliquer **pourquoi**. La vraie réponse est : "REAL est précis pour la plupart des usages, mais pas pour la monnaie à cause de la base 2 du flottant qui ne représente pas exactement les fractions décimales courantes."

---

## Q2.2 — Tu as une validation Flask, pourquoi AUSSI des CHECK en DB ?

🟢 **Réponse minimale :**
"Defense in depth. Si Flask est bypassé (bug, autre client qui attaque la DB directement), les contraintes DB rejettent encore les données invalides. C'est la dernière ligne de défense, la plus proche des données."

🔵 **Pour aller plus loin :**
"J'ai testé concrètement : `INSERT INTO products VALUES (?, -1)` est bloqué par `CHECK (price >= 0)`. Idem pour name vide, name > 200 chars, name NULL. La DB renvoie `IntegrityError`. Une vraie attaque qui contournerait Flask trouverait porte close."

---

## Q2.3 — Pourquoi limiter `name` à 200 caractères ?

🟢 **Réponse minimale :**
"Anti-DoS et anti-pollution. Sans limite, un attaquant pourrait insérer un nom de 1 Go → DB qui gonfle, page de recherche qui plante en affichant le résultat, RAM serveur saturée."

🔵 **Pour aller plus loin :**
"200 chars couvre largement les noms de produits réels (un nom de produit Amazon dépasse rarement 100 chars). C'est aussi cohérent avec le concept de **whitelist** : on définit ce qui est acceptable plutôt que de blacklister ce qui ne l'est pas."

---

## Q2.4 — Pourquoi `AUTOINCREMENT` ?

🟢 **Réponse minimale :**
"Pour que les IDs ne soient jamais réutilisés. Si je supprime le produit 42 et que SQLite donne l'id 42 à un autre produit plus tard, mes anciens logs mentionnant 'produit 42' deviennent trompeurs. AUTOINCREMENT préserve la traçabilité."

🔵 **Pour aller plus loin :**
"Sans AUTOINCREMENT, SQLite utilise `MAX(id) + 1`, donc si la dernière ligne est supprimée son id peut être réutilisé. AUTOINCREMENT maintient un compteur dans la table interne `sqlite_sequence` qui ne décroît jamais. Coût : très léger en perf (un INSERT supplémentaire dans sqlite_sequence)."

---

## Q2.5 — Pourquoi un index sur `name` ?

🟢 **Réponse minimale :**
"La page de recherche va faire des `WHERE name LIKE ...`. Sans index, c'est un full table scan O(n). Avec index, c'est O(log n)."

🔵 **Pour aller plus loin :**
"⚠️ Attention : un index sur LIKE ne fonctionne que pour les recherches préfixe (`LIKE 'iphone%'`). Pour `LIKE '%iphone%'` (substring), l'index n'est pas utilisé en SQL standard. Pour ce cas il faudrait FTS5 (Full-Text Search) de SQLite. Pour ce projet, recherche préfixe suffira."

---

## Q2.6 — Pourquoi séparer `schema.sql` et `init_db.py` ?

🟢 **Réponse minimale :**
"Séparation des préoccupations. Le SQL est un fichier pur, lisible par un DBA sans connaître Python. Le Python n'est qu'un lanceur."

🔵 **Pour aller plus loin :**
"Cette structure prépare aussi des migrations futures : on pourrait avoir `schema_v1.sql`, `migration_v1_to_v2.sql`, etc. Outils comme Alembic (pour SQLAlchemy) ou Flyway (généraliste) suivent ce principe. Pour notre scope, un seul `schema.sql` suffit."

---

## Q2.7 — Pourquoi `with sqlite3.connect(...) as conn:` ?

🟢 **Réponse minimale :**
"Context manager. Ferme la connexion proprement même si une exception est levée. Évite les fuites de file descriptors et les locks DB pendants."

🔵 **Pour aller plus loin :**
"En SQLite spécifiquement, le `with` commit aussi automatiquement à la sortie du bloc si tout s'est bien passé, et rollback en cas d'exception. C'est l'équivalent d'un try/finally + try/except, en plus court et plus sûr."

---

## Q2.8 — Pourquoi `CREATE TABLE IF NOT EXISTS` ?

🟢 **Réponse minimale :**
"Idempotence. Le script peut être lancé plusieurs fois sans erreur. Pratique en dev, indispensable pour des migrations en prod."

---

## Q2.9 — Pourquoi `created_at TEXT DEFAULT CURRENT_TIMESTAMP` ?

🟢 **Réponse minimale :**
"Audit trail. En cas d'incident sécurité (un produit suspect inséré), savoir QUAND il a été créé aide l'investigation. Coût quasi nul, valeur opérationnelle énorme."

🔵 **Pour aller plus loin :**
"SQLite n'a pas de type DATETIME natif, on utilise TEXT au format ISO 8601 (`YYYY-MM-DD HH:MM:SS`). C'est triable lexicographiquement, donc `ORDER BY created_at` fonctionne sans conversion."

---

# ÉTAPE 3 — App Flask minimale

*(à compléter)*

---

# ÉTAPE 4-5 — Pages vulnérables (insertion + recherche)

*(à compléter)*

---

# ÉTAPE 6 — Sécurisation des 6 vulnérabilités

*(à compléter avec une section par vuln : SQLi, XSS, CSRF, Clickjacking, Misconfig, Sensitive Data)*

---

# CONCEPTS TRANSVERSAUX (à toujours avoir en tête)

## Le triptyque CIA
**Confidentiality, Integrity, Availability** — base de toute analyse sécurité. Pour chaque vuln, demande-toi laquelle des 3 elle viole.

## Defense in depth
Pas une seule barrière, mais plusieurs couches. Si l'une cède, les autres tiennent. Exemple : validation côté client + validation côté serveur + parameterized queries + WAF.

## Principle of least privilege
Chaque composant n'a que les droits strictement nécessaires. Exemple : l'utilisateur DB de l'app n'a pas DROP TABLE.

## Fail securely
En cas d'erreur, le système doit échouer **fermé** (refuser l'accès) plutôt qu'ouvert (laisser passer). Exemple : si la validation d'un token plante, on rejette la requête, on ne l'accepte pas par défaut.

## Never trust user input
Toute donnée venant du client (formulaire, URL, header, cookie) est suspecte. Validation systématique côté serveur, **jamais** confiance dans le côté client.
