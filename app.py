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


@app.route("/")
def home() -> str:
    return render_template("home.html")


@app.route("/insert", methods=["GET", "POST"])
def insert():
    """
    Product insertion page.

    !! INTENTIONALLY VULNERABLE — this implementation will be hardened
    in step 6. Three deliberate weaknesses, marked below:

      FIXED  (SQLi):  parameterized query — name and price are passed
                      as separate parameters, never interpolated.
      VULN-2 (XSS):   no input validation/sanitization on `name`.
      VULN-3 (CSRF):  no CSRF token.
      VULN-4 (Info):  raw DB error string is returned to the client.
    """
    message = request.args.get("msg")
    error = None

    if request.method == "POST":
        name = request.form["name"]
        # Convert user-facing price (e.g. "9.99") to cents (999) for INTEGER storage.
        # round() avoids float drift: float("9.99") * 100 = 998.9999... without it.
        price = int(round(float(request.form["price"]) * 100))

        # FIX VULN-1: parameterized query.
        # name and price are passed as a tuple — the DB driver handles escaping.
        # No f-string, no concatenation, no executescript().
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO products (name, price) VALUES (?, ?)",
                    (name, price)
                )
            return redirect(url_for("insert", msg="Product inserted"))
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
