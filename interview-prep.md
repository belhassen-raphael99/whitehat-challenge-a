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

## Q3.1 — Pourquoi port 5001 et pas 5000 ?

🟢 **Réponse minimale :**
"Sur macOS depuis Monterey, AirPlay Receiver écoute sur 5000 par défaut. Conflit silencieux. J'ai utilisé 5001 pour éviter le piège."

🔵 **Pour aller plus loin :**
"C'est un exemple parfait de Security Misconfiguration dans la vraie vie : un dev qui ne le sait pas peut croire que son app tourne alors que c'est AirPlay qui répond à certaines requêtes. Bug très subtil à diagnostiquer."

---

## Q3.2 — Pourquoi `host="127.0.0.1"` et pas `"0.0.0.0"` ?

🟢 **Réponse minimale :**
"127.0.0.1 (loopback) limite l'accès à la machine locale. 0.0.0.0 expose le serveur sur toutes les interfaces réseau (WiFi, Ethernet, etc.). En dev avec debug=True, exposer en 0.0.0.0 ouvrirait le Werkzeug debugger à n'importe qui sur le WiFi → RCE."

🔵 **Pour aller plus loin :**
"En cybersécurité, la règle est : **principe de moindre exposition**. On expose le minimum nécessaire. En dev local, je n'ai besoin de personne d'autre que moi → 127.0.0.1 suffit. En prod, ce serait un reverse proxy (nginx) qui s'exposerait sur 0.0.0.0:443 et forwarderait à mon Flask sur 127.0.0.1:5001."

---

## Q3.3 — Qu'est-ce que le Werkzeug debugger et pourquoi c'est dangereux ?

🟢 **Réponse minimale :**
"Quand `debug=True`, Flask affiche une page d'erreur interactive avec une console Python en cas d'exception. Cette console permet d'exécuter du code arbitraire sur le serveur. Si l'app est exposée à Internet en mode debug → RCE pré-authentifiée."

🔵 **Pour aller plus loin :**
"Le debugger est protégé par un PIN, mais ce PIN est dérivé de manière déterministe d'infos serveur (username, machine ID, app path). Si l'attaquant peut leak ces infos via une autre vuln (LFI, info disclosure), il peut **calculer le PIN** et accéder à la console. Il y a des CVE et exploits publics. Donc règle absolue : `debug=False` en prod, point final."

⚠️ **Piège :** ne dis pas "le debugger est sécurisé par un PIN". C'est faux.

---

## Q3.4 — Qu'est-ce qu'on peut déduire d'un header `Server: Werkzeug/3.1.8 Python/3.14.4` ?

🟢 **Réponse minimale :**
"C'est de l'Information Disclosure (CWE-200). Ça révèle ma stack (Flask) et mes versions exactes. Un attaquant peut chercher des CVE spécifiques à ces versions et adapter ses payloads à Jinja2 (templating Flask)."

🔵 **Pour aller plus loin :**
"Plus large : ça permet aussi du **mass scanning**. Un attaquant qui découvre une CVE Werkzeug 3.1.8 peut scanner tout Internet à la recherche de ce header pour trouver des cibles. Bonne pratique : remplacer ou supprimer le header `Server`. On le fera en étape 6 via un middleware Flask."

---

## Q3.5 — Pourquoi `python app.py` plutôt que `flask run` ?

🟢 **Réponse minimale :**
"Toute la config (host, port, debug) est explicite dans le code. `flask run` cache la config dans des variables d'environnement → moins lisible, plus de magie."

🔵 **Pour aller plus loin :**
"Pour un projet d'audit, la lisibilité l'emporte sur l'idiomatisme. En prod réelle on utiliserait Gunicorn ou uWSGI de toute façon, donc `flask run` n'est pas non plus la cible finale."

---

## Q3.6 — Si tu déployais en prod, qu'est-ce que tu changerais dans app.py ?

🟢 **Réponse minimale (4 changements) :**
1. `debug=False`
2. Remplacer le serveur dev (Werkzeug) par un WSGI prod (Gunicorn ou uWSGI)
3. Mettre un reverse proxy (nginx ou Cloudflare) devant pour TLS termination
4. Supprimer le header `Server` ou le remplacer par une valeur générique

🔵 **Pour aller plus loin :**
"J'ajouterais aussi : variables d'env via `.env` (jamais en dur), logs structurés (JSON), monitoring (Sentry pour les erreurs, Prometheus pour les métriques), et rate-limiting (Flask-Limiter). Tout ça sort du scope du take-home mais je peux en parler."

---

# ÉTAPE 4 — Page d'insertion vulnérable

## Q4.1 — Pourquoi écrire du code volontairement vulnérable ?

🟢 **Réponse minimale :**
"Pour pouvoir prouver que ma protection fonctionne. Je joue l'attaque sur le code vulnérable, je montre qu'elle marche, je sécurise, je rejoue l'attaque, je montre qu'elle échoue. C'est la preuve concrète."

🔵 **Pour aller plus loin :**
"C'est aussi la méthode des cours de secure coding sérieux (PortSwigger Web Security Academy, OWASP Juice Shop). Sans cette confrontation, on apprend à écrire des bonnes pratiques sans comprendre **contre quoi** on se défend."

---

## Q4.2 — Décris la SQL Injection que tu as démontrée

🟢 **Réponse minimale :**
"Payload : `Hack', 0); DROP TABLE products; --`. La requête construite par concaténation devient `INSERT INTO products (name, price) VALUES ('Hack', 0); DROP TABLE products; --', 0)`. Le `'` ferme la string, le `;` enchaîne une nouvelle commande, le `DROP TABLE` détruit la table, le `--` neutralise la fin. Résultat : table effacée."

🔵 **Pour aller plus loin :**
"J'ai utilisé `executescript()` au lieu de `execute()` pour reproduire le pire cas réaliste. `execute()` n'autorise qu'une seule instruction SQL — un attaquant qui tombe sur du code utilisant `execute()` ne peut pas DROP TABLE, mais peut quand même faire d'autres dégâts (UNION SELECT pour exfiltrer, OR 1=1 pour bypass auth)."

⚠️ **Piège :** ne dis pas "j'ai exploité executescript". L'exécutsript n'est PAS la vuln — la vuln est la **concaténation**. executescript juste **amplifie** son impact.

---

## Q4.3 — Décris l'XSS stocké que tu as démontré

🟢 **Réponse minimale :**
"J'ai stocké `<img src=x onerror=alert(1)>` comme nom de produit. La DB l'a accepté (texte conforme aux CHECK). Quand la page de recherche affichera ce nom sans escape, le navigateur exécutera le JS de l'attribut `onerror`."

🔵 **Pour aller plus loin :**
"C'est de la **stored XSS** : le payload reste en DB et déclenche pour CHAQUE visiteur de la page. Variante la plus grave car elle persiste. Variante moins grave : reflected XSS (payload dans l'URL, ne touche que la victime du lien)."

⚠️ **Pourquoi `<img onerror>` et pas `<script>` ?** Parce que mon payload SQL contenait initialement des `'` qui cassaient ma syntaxe SQL. `<img src=x onerror=alert(1)>` ne contient aucun quote → traverse la SQL sans dommage.

---

## Q4.4 — Pourquoi les CHECK DB n'ont pas bloqué l'XSS ?

🟢 **Réponse minimale :**
"Une contrainte ne couvre qu'un type d'attaque. CHECK valide la longueur, le signe, les valeurs énumérées. Elle ne sait pas ce qu'est du HTML. XSS exige un escape à l'affichage, pas une validation à l'entrée."

🔵 **Pour aller plus loin :**
"Idéalement, on combine les deux : valider à l'entrée (rejeter `<script>` dans un nom de produit, par exemple), ET échapper à la sortie (Jinja2 auto-escape). Si on ne devait choisir qu'un seul, l'escape à la sortie est plus robuste car il fonctionne quel que soit l'input."

---

## Q4.5 — Comment tu vas fixer ces vulns en étape 6 ?

🟢 **Réponse minimale (4 fixes) :**
1. **SQLi** : passer à `cursor.execute("INSERT ... VALUES (?, ?)", (name, price))` — paramètres séparés, jamais concaténés.
2. **XSS** : Jinja2 escape par défaut, je laisse faire (et je vérifie qu'aucun `|safe` traîne).
3. **CSRF** : ajouter Flask-WTF avec `CSRFProtect(app)` + `{{ form.csrf_token }}` dans le template.
4. **Info disclosure** : remplacer le message d'erreur brut par un message générique côté client + log côté serveur.

🔵 **Pour aller plus loin :**
"En bonus : ajouter validation Flask explicite (whitelist) en plus des CHECK DB (defense in depth), et headers de sécurité (CSP, X-Frame-Options, X-Content-Type-Options) via un middleware after_request."

---

## Q4.6 — C'est quoi `executescript()` vs `execute()` vs `executemany()` ?

🟢 **Réponse minimale :**
- `execute(sql, params)` : 1 instruction SQL, paramétrable. Standard.
- `executemany(sql, list_of_params)` : 1 instruction, exécutée N fois avec différents params. Bulk insert.
- `executescript(sql)` : N instructions séparées par `;`, **non-paramétrable**. Pour scripts d'init.

🔵 **Pour aller plus loin :**
"`executescript` ne supporte pas les paramètres, donc c'est le candidat parfait pour les schémas (un fichier `.sql` lu et exécuté). Mais l'utiliser pour traiter de l'input utilisateur est dangereux : il transforme une SQLi 'limitée' (1 statement) en SQLi 'totale' (N statements). C'est exactement ce que j'ai démontré dans la version vulnérable."

---

# ÉTAPE 5 — Page de recherche vulnérable

## Q5.1 — Pourquoi l'XSS se déclenche sur la recherche et pas sur l'insertion ?

🟢 **Réponse minimale :**
"Stored XSS = 2 temps. L'insertion stocke le payload en DB sans le réafficher. La recherche le relit et l'injecte dans le HTML avec `| safe` → le navigateur l'exécute. Le danger est là, pas au moment du stockage."

🔵 **Pour aller plus loin :**
"C'est la différence entre stored XSS et reflected XSS. Stored : payload persistant en DB, touche tous les visiteurs qui voient la page. Reflected : payload dans l'URL, ne touche que la victime du lien. Stored est plus grave car il persiste."

---

## Q5.2 — Qu'est-ce que `| safe` dans Jinja2 et pourquoi c'est un red flag ?

🟢 **Réponse minimale :**
"`| safe` désactive l'auto-escape Jinja2. `{{ '<script>' }}` → `&lt;script&gt;` (safe). `{{ '<script>' | safe }}` → `<script>` exécuté par le navigateur."

🔵 **Pour aller plus loin :**
"En code review, la présence de `| safe` doit toujours lever une alerte : est-ce que la valeur vient d'une source de confiance (HTML hardcodé) ou d'une source utilisateur/DB ? Si c'est une source utilisateur → vulnérabilité XSS. La règle : jamais de `| safe` sur des données dynamiques."

⚠️ **Piège classique :** les devs ajoutent `| safe` parce que leurs balises HTML dans les données ne s'affichent pas correctement. C'est la mauvaise solution. La bonne : utiliser un sanitizer type Bleach (Python) qui autorise certaines balises mais bloque les scripts.

---

## Q5.3 — Décris l'attaque UNION SELECT

🟢 **Réponse minimale :**
"Payload : `x' UNION SELECT 1,'HACKED',0,'2026-01-01'--`. Le UNION enchaîne un second SELECT avec des valeurs forgées. En prod, `x' UNION SELECT 1,password,0,email FROM users--` exfiltre tous les mots de passe."

🔵 **Pour aller plus loin :**
"UNION SELECT nécessite que le nombre de colonnes soit identique dans les deux SELECT. D'abord l'attaquant fait du tâtonnement : `' ORDER BY 1--`, `' ORDER BY 2--`, etc. jusqu'à trouver l'erreur → détermine le nombre de colonnes. Ensuite `UNION SELECT NULL,NULL,NULL,NULL--` pour trouver les types. Puis il injecte les vraies valeurs. Processus systématique."

---

## Q5.4 — Décris l'attaque OR 1=1

🟢 **Réponse minimale :**
"Payload : `' OR '1'='1`. La clause WHERE devient `LIKE '%' OR '1'='1%'` → condition toujours vraie → retourne TOUS les enregistrements."

🔵 **Pour aller plus loin :**
"En contexte de login (`WHERE username='' AND password=''`), le payload `admin'--` commente le check password : `WHERE username='admin'--' AND password=''` → connexion sans mot de passe. C'est l'SQLi la plus médiatisée (cf. XKCD 'Little Bobby Tables')."

---

## Q5.5 — Quelle différence entre `execute()` et `executescript()` sur la sécurité ?

🟢 **Réponse minimale :**
"`execute()` n'exécute qu'une seule instruction. `executescript()` exécute un script multi-instructions. En version vulnérable j'ai utilisé `executescript()` sur l'INSERT pour permettre le `DROP TABLE`. Pour la recherche, `execute()` suffit à démontrer l'exfiltration (UNION SELECT)."

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
