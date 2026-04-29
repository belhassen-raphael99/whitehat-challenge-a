# Guide de présentation — ligne par ligne

> Ce fichier te permet de présenter et défendre **chaque ligne de code**
> du projet face à un pentester senior ou un auditeur applicatif.
>
> Structure : pour chaque bloc de code, tu trouveras :
> - ce que ça fait techniquement
> - pourquoi ça a été écrit comme ça
> - la question probable de l'intervieweur
> - la réponse modèle
>
> Lis à voix haute. Reformule avec tes mots. Ne récite pas.

---

# FICHIER 1 — `schema.sql`

```sql
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL CHECK (length(name) > 0 AND length(name) <= 200),
    price       INTEGER NOT NULL CHECK (price >= 0),
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
```

---

## `CREATE TABLE IF NOT EXISTS`

**Ce que ça fait :** crée la table uniquement si elle n'existe pas déjà.

**Pourquoi :** idempotence. On peut relancer `python init_db.py` 10 fois sans erreur.
En prod, c'est critique pour les migrations (tu ne veux pas que ton script de déploiement
plante parce que la table existe déjà).

**Question probable :** *"Pourquoi pas juste `CREATE TABLE` ?"*

**Réponse :** "`CREATE TABLE` plante si la table existe (`OperationalError: table already exists`).
`IF NOT EXISTS` rend le script safe à rejouer — bonne pratique pour tout script de migration."

---

## `id INTEGER PRIMARY KEY AUTOINCREMENT`

**Ce que ça fait :** colonne d'identifiant auto-incrémenté. Chaque INSERT reçoit
un id unique qui ne décroît jamais.

**Pourquoi AUTOINCREMENT et pas juste `INTEGER PRIMARY KEY` ?**
Sans `AUTOINCREMENT`, SQLite utilise `MAX(id) + 1`. Si le produit 42 est supprimé,
le prochain INSERT peut récupérer l'id 42. Tous les logs qui disaient "produit 42 = iPhone"
deviennent faux — c'est un problème d'audit trail.
Avec `AUTOINCREMENT`, SQLite maintient un compteur dans `sqlite_sequence` qui ne régresse
jamais. L'id 42 supprimé reste mort pour toujours.

**Question probable :** *"C'est quoi l'inconvénient d'AUTOINCREMENT ?"*

**Réponse :** "Très léger overhead : chaque INSERT écrit aussi dans la table interne
`sqlite_sequence`. En pratique, négligeable pour ce scope. Le trade-off vaut la traçabilité."

---

## `name TEXT NOT NULL CHECK (length(name) > 0 AND length(name) <= 200)`

**Ce que ça fait :** trois contraintes en une ligne :
1. `TEXT` — le type (SQLite est faiblement typé, le type est indicatif)
2. `NOT NULL` — refuse les NULL explicites
3. `CHECK (length(name) > 0 AND length(name) <= 200)` — refuse les chaînes vides et les noms trop longs

**Pourquoi une limite à 200 caractères ?**
Anti-DoS et anti-pollution. Sans limite, un attaquant insère un nom de 10 Mo → la DB gonfle,
la page de recherche plante en affichant le résultat, le serveur sature en RAM.
200 chars couvre largement tous les noms de produits réels (Amazon se limite à ~200 chars).

**Pourquoi `CHECK` en DB si Flask valide déjà ?**
Defense in depth. Si Flask est bypassé (autre script qui tape la DB directement, bug dans la
validation, curl en direct), la DB elle-même refuse les données invalides.
C'est la **dernière ligne de défense, la plus proche des données**.

**Question probable :** *"Tu valides deux fois — c'est pas du code redondant ?"*

**Réponse :** "Non, c'est deux couches indépendantes. Flask valide à l'entrée de l'application.
La DB valide à l'écriture. Si l'une est bypassée, l'autre tient. C'est exactement le principe
de defense in depth — pas une seule barrière, mais plusieurs couches."

---

## `price INTEGER NOT NULL CHECK (price >= 0)`

**Pourquoi INTEGER et pas REAL (float) ?**
IEEE 754 — les floats ne représentent pas exactement les fractions décimales courantes.
`9.99 * 100 = 998.9999999...` en float → `int()` donne 998, pas 999.
Le standard bancaire (Stripe, PayPal) : stocker en plus petite unité (centimes) en INTEGER.
À l'affichage on divise par 100.

**Pourquoi `CHECK (price >= 0)` ?**
Un prix négatif n'a pas de sens métier. Sans contrainte, un bug ou une injection partielle
pourrait insérer `price = -999` et casser l'affichage ou des calculs de total.

**Question probable :** *"Comment tu gères le prix $9.99 en entrée si tu stockes des centimes ?"*

**Réponse :** "Dans `validate_price()` : `float(raw)` → `int(round(value * 100))`.
Le `round()` est critique : sans lui, `9.99 * 100 = 998.999...` et `int()` tronque à 998.
`round()` donne 999.0 → `int()` donne 999. Exact."

---

## `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`

**Ce que ça fait :** enregistre automatiquement la date/heure d'insertion au format
ISO 8601 (`2026-04-23 14:32:11`).

**Pourquoi TEXT et pas DATETIME ?**
SQLite n'a pas de type DATETIME natif. TEXT au format ISO 8601 est triable
lexicographiquement — `ORDER BY created_at` fonctionne sans conversion.

**Pourquoi DEFAULT CURRENT_TIMESTAMP ?**
Audit trail. En cas d'incident (produit malveillant inséré), on sait exactement quand.
Coût quasi nul, valeur opérationnelle énorme.

---

## `CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)`

**Ce que ça fait :** crée un index B-tree sur la colonne `name`.

**Pourquoi ?**
La route `/search` fait `WHERE name LIKE ?`. Sans index → full table scan O(n).
Avec index → O(log n).

**Question probable :** *"Est-ce que l'index accélère vraiment LIKE ?"*

**Réponse :** "Partiellement. L'index accélère LIKE pour les recherches **préfixe** (`name%`).
Pour les recherches **substring** (`%name%`), SQLite ne peut pas utiliser l'index B-tree.
Pour du vrai full-text search on utiliserait l'extension FTS5 de SQLite.
Pour ce scope, acceptable — la démo fonctionne et j'ai documenté la limitation."

---

---

# FICHIER 2 — `init_db.py`

```python
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def init_db() -> None:
    schema_sql = SCHEMA_PATH.read_text()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema_sql)
        conn.commit()
    print(f"OK Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
```

---

## `from pathlib import Path` + `Path(__file__).parent / "database.db"`

**Ce que ça fait :** `__file__` est le chemin absolu du script Python en cours d'exécution.
`.parent` remonte d'un niveau (le dossier du script). `/ "database.db"` ajoute le nom de fichier.
Résultat : chemin absolu vers `database.db` **dans le même dossier que le script**, quel que
soit le répertoire courant depuis lequel on lance Python.

**Pourquoi pas juste `"database.db"` ?**
Un chemin relatif dépend du `cwd` au moment de l'exécution. Si tu lances
`python ~/whitehat-challenge-a/init_db.py` depuis `/tmp`, le fichier atterrit dans `/tmp`.
`Path(__file__).parent` est toujours correct, peu importe d'où tu lances le script.

---

## `SCHEMA_PATH.read_text()` puis `conn.executescript(schema_sql)`

**Pourquoi séparer le SQL dans `schema.sql` plutôt que l'écrire en Python ?**
Séparation des préoccupations. Le SQL est un fichier pur — lisible par un DBA sans
connaître Python. `executescript()` accepte du SQL multi-statements (CREATE TABLE + CREATE INDEX).

**Pourquoi `executescript()` ici mais pas dans les routes Flask ?**
`executescript()` ne supporte pas les paramètres. Il est fait pour les scripts d'init
(fichiers `.sql` sous notre contrôle, jamais de l'input utilisateur).
Dans les routes Flask, tout input utilisateur passe par `execute(sql, params)` — jamais
`executescript()`.

---

## `with sqlite3.connect(DB_PATH) as conn:`

**Ce que ça fait :** context manager. À la sortie du bloc :
- si tout s'est bien passé → commit automatique
- si une exception → rollback automatique
- dans les deux cas → connexion fermée proprement

**Sans `with` ?** Si une exception est levée entre `connect()` et `close()`, la connexion
reste ouverte → leak de file descriptor → lock DB pendant qui peut bloquer d'autres processus.

---

## `if __name__ == "__main__": init_db()`

**Ce que ça fait :** `init_db()` n'est appelée que si le script est **exécuté directement**
(`python init_db.py`). Si le module est **importé** (`from init_db import init_db`),
le bloc ne s'exécute pas.

**Pourquoi c'est important ?**
Si tu faisais `import init_db` depuis un test ou depuis `app.py`, le script ne détruirait
pas accidentellement la DB en production. C'est la convention Python standard.

---

---

# FICHIER 3 — `app.py` (le fichier le plus important)

---

## Imports et setup initial

```python
import logging
import os
import sqlite3
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.serving import WSGIRequestHandler
```

**`logging`** — module stdlib Python pour les logs structurés. On l'utilise à la place de
`print()` pour logger les erreurs DB côté serveur sans les exposer au client.

**`os`** — pour lire les variables d'environnement (`os.environ.get("FLASK_ENV")`).

**`WSGIRequestHandler`** — classe Werkzeug qui gère chaque requête HTTP au niveau TCP.
On l'importe pour overrider le header `Server` injecté avant même que Flask entre en jeu.

---

## Masquage du header Server (niveau TCP)

```python
WSGIRequestHandler.server_version = "Web Server"
WSGIRequestHandler.version_string = lambda self: "Web Server"
```

**Problème :** `curl -i` sur l'app vulnérable révélait `Server: Werkzeug/3.1.8 Python/3.14.4`.
C'est de l'Information Disclosure (CWE-200) — ça révèle le framework, la version exacte,
et la version Python. Un attaquant peut chercher des CVE spécifiques à Werkzeug 3.1.8.

**Pourquoi deux lignes ?**
- `server_version` est la chaîne statique `"Werkzeug/3.1.8"` utilisée pour construire le header.
- `version_string()` est la méthode qui assemble la chaîne finale. Sans l'override de la
  méthode, Werkzeug peut quand même injecter la version Python en reconstruisant le header.
- Les deux doivent être neutralisés pour un masquage complet.

**Question probable :** *"Mais tu as aussi un `after_request` qui set le Server header —
pourquoi les deux ?"*

**Réponse :** "Deux sources différentes. `WSGIRequestHandler` injecte le header au niveau
**connexion TCP** (HTTP/1.1 layer). `@after_request` s'exécute au niveau **réponse Flask**.
Ce sont deux mécanismes indépendants. Le `after_request` ne peut pas overrider ce que
Werkzeug a déjà écrit au niveau TCP sur certaines versions. On fixe les deux pour être certain."

---

## Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)
```

**Pourquoi `logging` et pas `print()` ?**
`print()` n'a pas de niveaux (INFO, WARNING, ERROR), pas de timestamps, pas de filtrage.
`logging` permet de router les erreurs vers un fichier, un SIEM, ou Sentry en production
en changeant juste la config — sans toucher le code applicatif.

**`__name__`** — le nom du module courant (`app` ou `__main__`). Permet de filtrer les logs
par module dans un projet multi-fichiers.

---

## Flask app + SECRET_KEY

```python
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-only-key-CHANGE-IN-PRODUCTION"
)
```

**Pourquoi `SECRET_KEY` ?**
Flask-WTF signe les tokens CSRF avec HMAC en utilisant cette clé. Sans elle, Flask lèverait
une erreur au démarrage. Si deux requêtes utilisent des clés différentes, les tokens sont invalides.

**Pourquoi `os.environ.get()` avec un fallback ?**
En dev, la clé par défaut est pratique (pas besoin de config). En prod, on injecte une valeur
aléatoire forte via variable d'environnement. **Jamais** de clé secrète hardcodée en prod —
elle serait dans le code source, dans le git history, potentiellement publique.

**Comment générer une bonne clé pour la prod ?**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
export SECRET_KEY=<la valeur>
```

---

## CSRFProtect

```python
csrf = CSRFProtect(app)
```

**Ce que ça fait :** active la protection CSRF sur **tous** les formulaires POST/PUT/PATCH/DELETE.
Chaque requête de ce type doit contenir un champ `csrf_token` valide et signé.
Une requête sans token → HTTP 400 automatique.

**Question probable :** *"Comment ça marche exactement un token CSRF ?"*

**Réponse :**
1. À chaque GET du formulaire, Flask génère un token aléatoire signé avec HMAC (SECRET_KEY).
2. Le token est inséré dans le HTML via `{{ csrf_token() }}` (champ caché).
3. Quand le formulaire est soumis, Flask vérifie le token.
4. Un site malveillant ne peut pas lire le token depuis notre page (same-origin policy).
5. Donc son POST forgé ne contient pas de token valide → rejeté avec HTTP 400.

---

## Middleware `@after_request` — headers de sécurité

```python
@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self'; "
        "script-src 'none'; "
        "object-src 'none';"
    )
    response.headers["Server"] = "Web Server"
    return response
```

**`@after_request`** — décorateur Flask qui exécute cette fonction sur **chaque réponse**,
quelle que soit la route. C'est le bon endroit pour les headers transversaux — un seul
endroit à maintenir, pas de risque d'oublier une route.

### `X-Frame-Options: DENY`

Interdit à n'importe quel site d'intégrer notre app dans un `<iframe>`.
Protection contre le **Clickjacking** : un attaquant ne peut pas superposer notre app
(transparente) par-dessus son site pour tromper l'utilisateur en lui faisant cliquer sur
nos boutons à son insu.

### `X-Content-Type-Options: nosniff`

Interdit au navigateur de "deviner" le Content-Type d'une réponse.
Exemple d'attaque sans ce header : si un attaquant réussit à héberger un fichier `.jpg`
qui contient en réalité du JS, certains navigateurs l'exécutent quand même.
`nosniff` force le navigateur à respecter le Content-Type déclaré.

### `Referrer-Policy: strict-origin-when-cross-origin`

Contrôle ce que le navigateur envoie dans le header `Referer` quand l'utilisateur
clique sur un lien externe. `strict-origin-when-cross-origin` : on envoie l'origine
(le domaine) mais pas le chemin complet. Évite de leaker des URLs internes
(ex : `/admin/edit/42`) à des sites tiers.

### `Content-Security-Policy`

```
default-src 'self'     → toutes les ressources (images, fonts, etc.) depuis notre domaine uniquement
style-src 'self'       → CSS depuis notre domaine uniquement
script-src 'none'      → AUCUN JS autorisé (ni inline, ni externe)
object-src 'none'      → pas de plugins (Flash, etc.)
```

C'est le backstop XSS côté navigateur. Même si un payload XSS passait Jinja2
(bug hypothétique), le navigateur **refuserait d'exécuter le script** parce que la CSP
dit `script-src 'none'`. Defense in depth en dernier recours.

**Question probable :** *"Pourquoi `script-src 'none'` si tu n'as pas de JS du tout ?"*

**Réponse :** "Précisément parce que je n'ai pas de JS — la valeur `'none'` est la plus
restrictive possible. Si demain un dev ajoute un `<script>` inline sans réfléchir, la CSP
le bloque et génère une erreur console visible. C'est aussi une déclaration d'intention :
cette app n'a pas besoin de JS."

---

## Handlers d'erreur génériques

```python
@app.errorhandler(400)
def bad_request(e):
    logger.warning("400 Bad Request: %s", e)
    return render_template("error.html", code=400, message="Bad request."), 400

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error("500 Internal Server Error: %s", e)
    return render_template("error.html", code=500, message="An internal error occurred. Please try again."), 500
```

**Problème résolu :** sans ces handlers, Flask affiche une page d'erreur par défaut qui
contient le message d'exception brut (ex : `sqlite3.IntegrityError: CHECK constraint failed`).
C'est du **CWE-209 : Information Exposure Through an Error Message**.

**Deux niveaux :**
- Le message d'erreur réel → `logger.error()` → logs serveur uniquement
- Le client → message générique → pas de fuite de structure DB, de framework, de stack trace

**Question probable :** *"Le 404 n'a pas de `logger` — pourquoi ?"*

**Réponse :** "Un 404 n'est pas une erreur serveur, c'est un comportement normal (URL inexistante).
On ne veut pas polluer les logs avec des 404 fréquents (scanners automatiques,
liens morts). Le 400 a un WARNING car c'est souvent un token CSRF invalide — signal utile.
Le 500 a un ERROR car c'est toujours un vrai problème à investiguer."

---

## Validation Flask — `validate_name()` et `validate_price()`

```python
def validate_name(name: str) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Product name cannot be empty."
    if len(name) > 200:
        return False, "Product name must be 200 characters or less."
    return True, ""

def validate_price(raw: str) -> tuple[bool, str, int]:
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return False, "Price must be a valid number.", 0
    if value < 0:
        return False, "Price cannot be negative.", 0
    return True, "", int(round(value * 100))
```

**Approche whitelist :** on définit ce qui est valide (longueur 1-200, nombre >= 0).
Tout le reste est rejeté. C'est l'opposé d'une blacklist (qui essaie de lister le mal —
toujours incomplète).

**`name.strip()`** — un nom qui ne contient que des espaces passerait le check `if not name`
sans strip. `"   "` a une longueur de 3 mais est sémantiquement vide. Le strip normalise.

**`int(round(value * 100))`** — conversion float → centimes.
- `float("9.99")` → `9.99`
- `9.99 * 100` → `998.9999999999999` (IEEE 754)
- `round(998.999...)` → `999.0`
- `int(999.0)` → `999`
Sans `round()`, le prix `$9.99` serait stocké comme 998 centimes (= `$9.98`). Bug silencieux.

**Retour `tuple[bool, str, int]` :** pattern explicite — la route sait exactement si la
validation a passé, pourquoi elle a échoué, et quelle est la valeur convertie.
Pas d'exception, pas de valeur magique.

---

## Route `/insert` — GET + POST

```python
@app.route("/insert", methods=["GET", "POST"])
def insert():
    message = request.args.get("msg")
    error = None

    if request.method == "POST":
        name = request.form.get("name", "")
        raw_price = request.form.get("price", "")

        name_ok, name_err = validate_name(name)
        price_ok, price_err, price = validate_price(raw_price)

        if not name_ok:
            error = name_err
        elif not price_ok:
            error = price_err
        else:
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute(
                        "INSERT INTO products (name, price) VALUES (?, ?)",
                        (name, price)
                    )
                return redirect(url_for("insert", msg="Product inserted successfully."))
            except sqlite3.Error as e:
                logger.error("DB error on insert: %s", e)
                error = "An error occurred. Please try again."

    return render_template("insert.html", message=message, error=error)
```

### `request.args.get("msg")` — lecture du query param

Après un INSERT réussi, on redirige vers `/insert?msg=Product+inserted+successfully.`
Le message de succès est lu depuis l'URL, pas depuis une session ou un flash.
Ça implémente le pattern **POST-Redirect-GET** (PRG).

**Question probable :** *"C'est quoi le pattern POST-Redirect-GET ?"*

**Réponse :** "Problème : si tu soumets un formulaire POST et appuies sur F5,
le navigateur resoummet le POST → double insertion. Solution PRG : après un POST
réussi, on fait un redirect HTTP 302 vers une page GET. F5 sur la page GET ne resoummet
pas le formulaire. C'est le comportement attendu sur tout formulaire web."

### `request.form.get("name", "")` — valeur par défaut ""

Si le champ est absent de la requête (client mal formé), on obtient `""` au lieu d'une
`KeyError`. `validate_name("")` retournera `False, "cannot be empty"` — comportement
propre sans exception non-catchée.

### Requête paramétrée

```python
conn.execute(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    (name, price)
)
```

Les `?` sont des **placeholders**. Le driver `sqlite3` passe les valeurs séparément du SQL.
Le payload `Hack', 0); DROP TABLE products; --` devient la chaîne littérale stockée dans
`name` — jamais interprétée comme SQL.

**Question probable :** *"Comment le driver empêche l'injection ?"*

**Réponse :** "Le driver envoie la requête SQL et les paramètres dans des messages distincts
au moteur SQLite. Le moteur compile d'abord la requête SQL (avec ses `?`) en bytecode,
puis substitue les paramètres à l'exécution — en s'assurant qu'ils sont traités comme
des valeurs, jamais comme du code SQL. Physiquement impossible d'injecter du SQL via un
paramètre."

### `except sqlite3.Error as e`

Attrape toutes les erreurs SQLite (`OperationalError`, `IntegrityError`, etc.).
Le `e` réel va dans les logs (`logger.error`). Le client reçoit une string générique.

**Pourquoi `sqlite3.Error` et pas juste `Exception` ?**
On attrape spécifiquement les erreurs DB — pas plus large. Si une autre exception
inattendue se produit (ex : erreur dans `render_template`), elle se propage normalement
et est catchée par le `@app.errorhandler(500)`. Chaque couche attrape ce qui la concerne.

---

## Route `/search`

```python
@app.route("/search")
def search():
    q = request.args.get("q", "")
    results = []

    if q:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                results = conn.execute(
                    "SELECT id, name, price, created_at FROM products WHERE name LIKE ?",
                    (f"%{q}%",)
                ).fetchall()
        except sqlite3.Error as e:
            logger.error("DB error on search: %s", e)
            return render_template(
                "error.html", code=500,
                message="An error occurred. Please try again."
            ), 500

    return render_template("search.html", q=q, results=results)
```

### `request.args.get("q", "")` — GET params

La recherche utilise GET (pas POST) — c'est intentionnel. Une recherche est idempotente
(pas d'effet de bord), shareable via URL, bookmarkable. Ça correspond à la sémantique HTTP.

### Requête LIKE paramétrée

```python
"SELECT ... WHERE name LIKE ?", (f"%{q}%",)
```

Le pattern `%{q}%` est construit en Python (pas dans le SQL), puis passé comme **paramètre**.
Le SQL compilé contient un seul `?` — pas de concaténation de SQL.

**Question probable :** *"Le `f"%{q}%"` n'est-il pas une concaténation dangereuse ?"*

**Réponse :** "Non. La concaténation se fait dans le **paramètre Python**, pas dans
la **chaîne SQL**. Le SQL qui atteint le moteur est littéralement `WHERE name LIKE ?`.
Le pattern `%hack'; DROP TABLE--` est passé comme valeur, donc cherché littéralement
dans les noms de produits. Aucun produit ne correspond → 0 résultats."

### `if q:` — guard avant la requête

Si `q` est vide (accès direct à `/search` sans paramètre), on ne touche pas la DB.
On retourne `results = []` et le template affiche la page vide proprement.
Évite une requête SQL inutile `WHERE name LIKE '%%'` qui retournerait toute la table.

---

## Mode debug contrôlé par env

```python
if __name__ == "__main__":
    is_production = os.environ.get("FLASK_ENV") == "production"
    app.run(host="127.0.0.1", port=5001, debug=not is_production)
```

**`debug=True` en dev :** auto-reload sur modification de fichier, page d'erreur
interactive Werkzeug.

**Danger de `debug=True` en prod :** le Werkzeug interactive debugger affiche une
console Python dans le navigateur en cas d'exception. N'importe qui peut exécuter
du code Python arbitraire sur le serveur. C'est une **RCE pré-authentifiée**.

**Atténuation en dev :** `host="127.0.0.1"` bind uniquement le loopback.
Le debugger n'est accessible que depuis la machine locale.

**Contrôle par env :** en prod, `FLASK_ENV=production` → `is_production=True` →
`debug=False`. On ne hardcode pas `False` dans le code car ça rendrait le dev pénible
(no auto-reload). La variable d'environnement est le bon mécanisme.

---

---

# FICHIER 4 — `templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Whitehat Challenge A{% endblock %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
```

**`lang="en"`** — accessibilité et SEO. Les lecteurs d'écran adaptent la prononciation.

**`charset="UTF-8"`** — encoding explicite. Sans lui, certains navigateurs peuvent
mal interpréter des caractères spéciaux dans les inputs → vecteur d'attaque charset
(historique, mais bonne pratique).

**`{% block title %}`** — mécanisme d'héritage Jinja2. Chaque template enfant
override ce bloc. Si pas d'override → valeur par défaut "Whitehat Challenge A".

**`url_for('static', filename='style.css')`** — génère le bon chemin vers le fichier
statique, indépendamment du `APPLICATION_ROOT` ou du reverse proxy.
Ne jamais hardcoder `/static/style.css` — ça peut casser en prod.

---

## Navigation

```html
<nav class="site-nav">
  <a href="{{ url_for('home') }}">Home</a>
  <a href="{{ url_for('insert') }}">Insert</a>
  <a href="{{ url_for('search') }}">Search</a>
</nav>
```

**`url_for('home')`** — génère l'URL de la route nommée `home` dans `app.py`.
Si demain on change `/` en `/home`, il suffit de modifier la route Flask —
tous les liens du template se mettent à jour automatiquement.

---

## Dev banner

```html
<div class="dev-banner">
  Development mode — hardened build (step 6 complete).
  Run with FLASK_ENV=production to disable this banner.
</div>
```

Rappel visuel que le serveur tourne en mode dev. Informe le développeur que
`FLASK_ENV=production` est le chemin vers la prod (et que cette bannière disparaîtra).

---

---

# FICHIER 5 — `templates/insert.html`

```html
<form method="POST" action="{{ url_for('insert') }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>
```

**`method="POST"`** — l'insertion est une action qui modifie l'état (idempotent=non).
POST est sémantiquement correct (vs GET qui ne devrait pas avoir d'effets de bord).

**`<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`**
Le token CSRF est invisible dans l'UI. Flask-WTF le valide côté serveur sur chaque POST.
Un site malveillant ne peut pas lire cette valeur (same-origin policy) → son POST forgé
est rejeté avec HTTP 400.

```html
<input type="number" id="price" name="price" min="0" step="0.01" placeholder="0.00" required>
```

**`type="number"`** — le navigateur affiche un clavier numérique sur mobile et bloque
les caractères non-numériques côté client. C'est une UX hint, **pas** une protection
de sécurité — le serveur valide indépendamment.

**`min="0" step="0.01"`** — empêche les prix négatifs et limite aux centimes dans l'UI.

**`required`** — validation HTML5 côté client. Confort utilisateur uniquement —
le serveur valide aussi (un attaquant peut soumettre sans `required` via curl/Postman).

---

---

# FICHIER 6 — `templates/search.html`

```html
{% for row in results %}
<tr>
  <td class="id">{{ row[0] }}</td>
  <td class="name">{{ row[1] }}</td>
  <td class="price">${{ "%.2f" % (row[2] / 100) }}</td>
  <td class="date">{{ row[3][:10] }}</td>
</tr>
{% endfor %}
```

### `{{ row[1] }}` — sans `| safe`

C'est ici que la protection XSS se joue. Jinja2 auto-escape est actif sur tous les
templates `.html`. `{{ row[1] }}` convertit automatiquement :
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&#39;`
- `&` → `&amp;`

Le payload `<img src=x onerror=alert(1)>` devient
`&lt;img src=x onerror=alert(1)&gt;` — le navigateur l'affiche comme texte, ne l'exécute pas.

**Ce qui était vulnérable (étape 5) :**
```html
<td class="name">{{ row[1] | safe }}</td>
```
`| safe` désactive l'auto-escape → le navigateur reçoit du HTML brut → exécute le JS.
Un seul filtre `| safe` mal placé suffit pour une XSS stockée.

### `"%.2f" % (row[2] / 100)`

Conversion centimes → dollars avec 2 décimales. `row[2]` est un INTEGER (ex: 999).
`999 / 100` = `9.99` (float). `"%.2f" % 9.99` = `"9.99"`. Propre et prévisible.

### `row[3][:10]`

`created_at` est stocké au format `"2026-04-23 14:32:11"`. `[:10]` garde uniquement
la date `"2026-04-23"`. L'heure exacte n'est pas pertinente pour l'affichage.

---

---

# FICHIER 7 — `templates/error.html`

```html
{% extends "base.html" %}
{% block title %}Error {{ code }} — Whitehat Challenge A{% endblock %}
{% block content %}
<div class="card">
  <h2>Error {{ code }}</h2>
  <p>{{ message }}</p>
  <div class="cta-row">
    <a class="cta" href="{{ url_for('home') }}">Back to home</a>
  </div>
</div>
{% endblock %}
```

Template minimaliste. Affiche uniquement :
- Le code HTTP (`400`, `404`, `500`)
- Un message générique contrôlé par le code Python (`"An error occurred. Please try again."`)
- Un lien de retour vers l'accueil

**Ce qui N'est PAS affiché :**
- La stack trace Python
- Le message d'exception brut (`sqlite3.IntegrityError: ...`)
- Le chemin de fichier ou la version de Flask
- Tout détail technique exploitable par un attaquant

---

---

# RÉCAP — Les 4 vulnérabilités et leurs fixes

## 1. SQL Injection

| | Vulnérable | Fixé |
|---|---|---|
| Mécanisme | `f"INSERT ... VALUES ('{name}', {price})"` + `executescript()` | `execute("INSERT ... VALUES (?, ?)", (name, price))` |
| Risque | `DROP TABLE products` via `;` dans le nom | Payload traité comme string littérale |
| Commit | — | `4efd292 security(sqli)` |

## 2. XSS stocké

| | Vulnérable | Fixé |
|---|---|---|
| Mécanisme | `{{ row[1] \| safe }}` dans search.html | `{{ row[1] }}` (auto-escape actif) |
| Risque | `<img onerror=alert(1)>` exécuté dans le navigateur | Rendu comme `&lt;img&gt;` — texte inerte |
| Commit | — | `0ad0694 security(xss)` |

## 3. CSRF

| | Vulnérable | Fixé |
|---|---|---|
| Mécanisme | Formulaire sans token | `CSRFProtect(app)` + `{{ csrf_token() }}` |
| Risque | N'importe quel site peut POST vers `/insert` | POST sans token valide → HTTP 400 |
| Commit | — | `067ca33 security(csrf)` |

## 4. Information disclosure

| | Vulnérable | Fixé |
|---|---|---|
| Server header | `Server: Werkzeug/3.1.8 Python/3.14.4` | `Server: Web Server` |
| Erreurs DB | `sqlite3.IntegrityError: CHECK constraint failed` dans la réponse | Message générique + log serveur |
| Debug mode | `debug=True` hardcodé | `debug = not (FLASK_ENV == 'production')` |
| Commit | — | `39988d7 security(headers)` |

---

---

# QUESTIONS PIÈGES — à ne pas rater

## "Ton app est vraiment sécurisée ?"

Bonne réponse : "Elle est sécurisée **pour ce scope**. Elle protège contre les
vulnérabilités applicables à une app CRUD sans authentification :
SQLi, XSS, CSRF, information disclosure, clickjacking.
Ce qui sort du scope documenté et justifié :
TLS (à gérer par le reverse proxy en prod),
rate limiting, WAF, SIEM. Ces couches existent, je peux les expliquer,
mais elles sortent du périmètre d'un take-home en local."

## "Pourquoi Flask et pas Django ?"

Bonne réponse : "Django a des protections auto (ORM paramétré, CSRF middleware actif
par défaut). C'est bien en prod, mais ça cache le mécanisme. Avec Flask,
chaque protection est explicite dans mon code — je peux montrer ligne par ligne
pourquoi elle est là et contre quoi elle protège. Pour un take-home de sécurité,
l'explicite gagne."

## "Est-ce que tu aurais XSS si tu utilisais Django ?"

Bonne réponse : "Non, car Django active l'auto-escape Jinja2/DTL par défaut et n'a pas
de `| safe` dans ses templates générés automatiquement. Mais un dev peut toujours
l'ajouter manuellement (`mark_safe()` en Django). La protection côté framework
ne dispense pas de comprendre le mécanisme."

## "Pourquoi SQLite et pas PostgreSQL ?"

Bonne réponse : "Pour ce scope : une table, pas de concurrence réseau, pas de besoin
d'utilisateurs DB distincts. SQLite est dans la stdlib Python — zéro setup.
Sur PostgreSQL en prod, j'utiliserais un user dédié avec `GRANT INSERT, SELECT` uniquement
— jamais `DROP`, `ALTER`. J'ai documenté ça dans `security-audit.md` item 4a."

## "Est-ce que tes `CHECK` constraints protègent contre XSS ?"

Bonne réponse : "Non, et c'est important de le comprendre. Les `CHECK` constraints
valident la **structure** des données (longueur, signe, type). Elles ne savent pas
ce qu'est du HTML ou du JS. `<img onerror=alert(1)>` est une string valide de 30 chars.
XSS exige un escape à **l'affichage** — c'est Jinja2 qui s'en charge, pas la DB."

## "Si demain tu mettais cette app en prod, qu'est-ce que tu ferais ?"

Bonne réponse (dans l'ordre) :
1. Remplacer le serveur dev Werkzeug par Gunicorn (`gunicorn -w 4 app:app`)
2. Mettre nginx devant (TLS, `server_tokens off`, compression, static files)
3. Générer une vraie SECRET_KEY aléatoire en env var
4. Passer `FLASK_ENV=production`
5. Ajouter Flask-Limiter (rate limiting anti-DoS)
6. Logs structurés JSON → SIEM
7. Si multi-utilisateurs : ajouter une couche d'auth (Flask-Login ou OAuth2)
8. Si PostgreSQL : user DB dédié avec permissions minimales

---

---

# SCRIPT DE PRÉSENTATION — comment ouvrir l'entretien

> Si l'intervieweur te dit "présente ton projet", voici le fil conducteur :

---

**"J'ai construit une app Flask + SQLite avec deux pages : insertion et recherche de produits.
L'approche que j'ai choisie est 'vulnérable d'abord, sécurisé ensuite' —
j'ai délibérément introduit les 4 vulnérabilités classiques applicables à ce scope,
je les ai démontrées avec des payloads réels, puis je les ai corrigées avec des commits
séparés. L'objectif : pouvoir prouver que chaque protection fonctionne, pas juste l'affirmer.**

**Le projet est structuré en 8 étapes documentées dans le git log. J'ai aussi produit
un audit de sécurité formel (`security-audit.md`) qui mappe chaque ligne de code
contre le référentiel de développement sécurisé White-Hat, et un rapport de tests
croisés (`cross-tests.md`) qui rejoue chaque attaque sur la version sécurisée —
8 tests, tous bloqués.**

**Vous voulez qu'on commence par les vulnérabilités, par le schéma DB, ou par l'architecture globale ?"**

---

Cette ouverture montre que tu :
- As une démarche structurée (pas juste du code)
- Comprends les attaques ET les défenses
- As anticipé les questions en documentant proactivement
- Laisses l'intervieweur choisir le fil — signe de maîtrise

---

*Fin du guide. Entraîne-toi à reformuler chaque réponse avec tes propres mots.*
*L'objectif n'est pas de réciter — c'est de comprendre assez bien pour improviser.*
