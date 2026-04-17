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

      VULN-1 (SQLi):  query is built with f-string concatenation
                      AND uses executescript() to enable multi-statement
                      payloads (worst-case scenario).
      VULN-2 (XSS):   no input validation/sanitization on `name`. A
                      payload like <script>alert(1)</script> is stored
                      verbatim and will fire when displayed (step 5).
      VULN-3 (CSRF):  no CSRF token. Any external site can submit a
                      cross-origin POST and insert a product on behalf
                      of any visitor.
      VULN-4 (Info):  raw DB error string is returned to the client on
                      failure — leaks schema details. Sensitive data
                      exposure (CWE-209).
    """
    message = request.args.get("msg")
    error = None

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]

        # VULN-1: f-string concatenation + executescript = SQLi paradise.
        # Same input could break out of the value and run arbitrary SQL,
        # including DROP TABLE.
        query = f"INSERT INTO products (name, price) VALUES ('{name}', {price})"

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.executescript(query)
            return redirect(url_for("insert", msg="Product inserted"))
        except sqlite3.Error as e:
            # VULN-4: raw error message returned to user.
            error = f"Database error: {e}"

    return render_template("insert.html", message=message, error=error)


if __name__ == "__main__":
    # host=127.0.0.1: bind to localhost only (NOT exposed to network)
    # port=5001: avoid macOS AirPlay collision on default port 5000
    # debug=True: auto-reload + debug page - DEV ONLY, never in production
    app.run(host="127.0.0.1", port=5001, debug=True)
