"""
Whitehat Challenge A - Flask web application.

Usage (development):
    python app.py

Then open http://127.0.0.1:5001 in your browser.

WARNING: this script runs Flask in development mode (debug=True,
built-in dev server). It is NOT suitable for production. See README
for production deployment notes.

WARNING (step 4): the /insert route is INTENTIONALLY VULNERABLE to
SQL Injection, stored XSS, and CSRF. These vulnerabilities are
demonstrated and then fixed in step 6. See security-audit.md.
"""
import logging
import os
import sqlite3
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.serving import WSGIRequestHandler

# Mask Werkzeug's own Server header injected at the connection level.
# after_request only controls app-level headers; this fixes the server-level one.
# In production (nginx/Gunicorn), the reverse proxy handles this instead.
WSGIRequestHandler.server_version = "Web Server"
WSGIRequestHandler.version_string = lambda self: "Web Server"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# SECRET_KEY is required by Flask-WTF to sign CSRF tokens.
# In production: set via environment variable, never hardcode.
# The fallback here is for local development only.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-only-key-CHANGE-IN-PRODUCTION"
)

# FIX VULN-3: CSRF protection.
# CSRFProtect validates the csrf_token field on every POST/PUT/PATCH/DELETE.
# A missing or invalid token returns HTTP 400 — the request is rejected.
csrf = CSRFProtect(app)

DB_PATH = Path(__file__).parent / "database.db"


# --- FIX VULN-5: Security headers (Clickjacking, Misconfiguration) ---

@app.after_request
def set_security_headers(response):
    """Inject security headers on every response."""
    # FIX Clickjacking: forbid this page from being embedded in an iframe.
    response.headers["X-Frame-Options"] = "DENY"
    # Prevent browsers from MIME-sniffing the content type.
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Limit referrer information sent to external sites.
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # CSP: only load resources from self, forbid inline scripts and objects.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self'; "
        "script-src 'none'; "
        "object-src 'none';"
    )
    # FIX VULN-6: mask the Server header — do not leak framework/version info.
    response.headers["Server"] = "Web Server"
    return response


# --- FIX VULN-6: Generic error pages (no stack traces or DB details) ---

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


# --- Input validation (whitelist approach) ---

def validate_name(name: str) -> tuple[bool, str]:
    """Whitelist validation for product name."""
    name = name.strip()
    if not name:
        return False, "Product name cannot be empty."
    if len(name) > 200:
        return False, "Product name must be 200 characters or less."
    return True, ""


def validate_price(raw: str) -> tuple[bool, str, int]:
    """Parse and validate price string → cents integer."""
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return False, "Price must be a valid number.", 0
    if value < 0:
        return False, "Price cannot be negative.", 0
    return True, "", int(round(value * 100))


@app.route("/")
def home() -> str:
    return render_template("home.html")


@app.route("/insert", methods=["GET", "POST"])
def insert():
    """
    Product insertion page.

    FIXED  (SQLi):  parameterized query.
    FIXED  (XSS):   whitelist validation rejects bad input server-side.
    VULN-3 (CSRF):  no CSRF token yet — fixed in next commit.
    VULN-4 (Info):  raw DB error string — fixed in a later commit.
    """
    message = request.args.get("msg")
    error = None

    if request.method == "POST":
        name = request.form.get("name", "")
        raw_price = request.form.get("price", "")

        # FIX VULN-2: server-side whitelist validation before touching the DB.
        name_ok, name_err = validate_name(name)
        price_ok, price_err, price = validate_price(raw_price)

        if not name_ok:
            error = name_err
        elif not price_ok:
            error = price_err
        else:
            # FIX VULN-1: parameterized query — driver handles escaping.
            # FIX VULN-2: input already validated above (whitelist).
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute(
                        "INSERT INTO products (name, price) VALUES (?, ?)",
                        (name, price)
                    )
                return redirect(url_for("insert", msg="Product inserted successfully."))
            except sqlite3.Error as e:
                # FIX VULN-4: log real error server-side, show generic message.
                logger.error("DB error on insert: %s", e)
                error = "An error occurred. Please try again."

    return render_template("insert.html", message=message, error=error)


@app.route("/search")
def search():
    """
    Product search page.

    !! INTENTIONALLY VULNERABLE — to be hardened in step 6:

      FIXED  (SQLi):  parameterized LIKE — pattern passed as parameter.
      VULN-2 (XSS):   results rendered with | safe in the template.
      VULN-4 (Info):  raw sqlite3.Error returned to client on failure.
    """
    q = request.args.get("q", "")
    results = []

    if q:
        # FIX VULN-1: parameterized LIKE query.
        # The wildcard pattern f"%{q}%" is passed as a parameter, not concatenated.
        # OR 1=1 and UNION SELECT payloads are now treated as literal strings.
        try:
            with sqlite3.connect(DB_PATH) as conn:
                results = conn.execute(
                    "SELECT id, name, price, created_at FROM products WHERE name LIKE ?",
                    (f"%{q}%",)
                ).fetchall()
        except sqlite3.Error as e:
            # FIX VULN-4: generic error to client, real error to server log.
            logger.error("DB error on search: %s", e)
            return render_template(
                "error.html", code=500,
                message="An error occurred. Please try again."
            ), 500

    return render_template("search.html", q=q, results=results)


if __name__ == "__main__":
    # FIX VULN-5: debug mode loaded from env, not hardcoded.
    # Development (default): FLASK_ENV unset or "development" → debug=True
    # Production:            FLASK_ENV=production              → debug=False
    is_production = os.environ.get("FLASK_ENV") == "production"
    app.run(host="127.0.0.1", port=5001, debug=not is_production)
