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
import sqlite3
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "database.db"


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
                # VULN-4: still raw error — fixed in a later commit
                error = f"Database error: {e}"

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
            # VULN-4: still raw error — fixed in a later commit
            return f"Database error: {e}", 500

    return render_template("search.html", q=q, results=results)


if __name__ == "__main__":
    # host=127.0.0.1: bind to localhost only (NOT exposed to network)
    # port=5001: avoid macOS AirPlay collision on default port 5000
    # debug=True: auto-reload + debug page - DEV ONLY, never in production
    app.run(host="127.0.0.1", port=5001, debug=True)
