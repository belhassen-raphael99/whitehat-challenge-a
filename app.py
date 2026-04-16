"""
Whitehat Challenge A - Flask web application.

Usage (development):
    python app.py

Then open http://127.0.0.1:5001 in your browser.

WARNING: this script runs Flask in development mode (debug=True,
built-in dev server). It is NOT suitable for production. See README
for production deployment notes.
"""
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home() -> str:
    return "<h1>Whitehat Challenge A</h1><p>Flask is running.</p>"


if __name__ == "__main__":
    # host=127.0.0.1: bind to localhost only (NOT exposed to network)
    # port=5001: avoid macOS AirPlay collision on default port 5000
    # debug=True: auto-reload + debug page - DEV ONLY, never in production
    app.run(host="127.0.0.1", port=5001, debug=True)
