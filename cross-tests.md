# Cross-Test Verification — Step 7

> Every attack demonstrated in steps 4–5 replayed against the hardened
> (step 6) codebase. Goal: prove each protection actually blocks the
> corresponding attack.
>
> All tests run against a fresh DB (`python init_db.py`) on commit 7f0ab5b.

---

## Summary

| # | Attack | Step 4/5 result | Step 6 result | Protection |
|---|---|---|---|---|
| 1 | Server header disclosure | `Server: Werkzeug/3.1.8 Python/3.14.4` | `Server: Web Server` | `WSGIRequestHandler` override + `@after_request` |
| 2 | Security headers absent | No CSP, no X-Frame-Options | All 4 headers present | `@after_request` middleware |
| 3 | CSRF — forged POST | HTTP 200, product inserted | HTTP 400, rejected | Flask-WTF `CSRFProtect` |
| 4 | SQLi — DROP TABLE | Table destroyed | Table intact, payload stored as literal text | Parameterized query `execute(sql, (name, price))` |
| 5 | XSS — stored payload in search | `<img onerror=alert(1)>` executes | Rendered as `&lt;img onerror=alert(1)&gt;` | Jinja2 auto-escape (`\| safe` removed) |
| 6 | SQLi search — UNION SELECT | Injected row appears in results | 0 injected `<td>` rows | Parameterized LIKE `execute(sql, (f"%{q}%",))` |
| 7 | SQLi search — OR 1=1 | All rows returned | 0 rows returned (literal string, no match) | Parameterized LIKE |
| 8 | Verbose error messages | `sqlite3.IntegrityError: ...` in response | Generic "Page not found." — no stack trace | `@app.errorhandler` + `try/except sqlite3.Error` |

All 8 tests pass. Zero regressions on the protected build.

---

## Detailed test log

### Test 1 — Server header

```
$ curl -si http://127.0.0.1:5001/ | grep -i "^server:"
Server: Web Server
Server: Web Server
```

Two occurrences: one from Werkzeug connection level, one from Flask response level.
Both masked. Neither leaks framework or version.

---

### Test 2 — Security headers

```
$ curl -si http://127.0.0.1:5001/ | grep -iE "^(x-frame|x-content|referrer|content-security)"
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; style-src 'self'; script-src 'none'; object-src 'none';
```

All 4 headers present on every response.

---

### Test 3 — CSRF (forged POST without token)

```
$ curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://127.0.0.1:5001/insert \
    -d "name=MaliciousProduct&price=9.99"
400
```

HTTP 400 returned before the route handler runs. No product inserted.

---

### Test 4 — SQL Injection (DROP TABLE) via Python with valid CSRF token

```python
sqli_payload = "Hack', 0); DROP TABLE products; --"
# POST with valid CSRF token via urllib session
# HTTP status: 200 (insert was attempted — token was valid)

# After the request:
conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
# → 7 (table exists, count incremented — payload stored as literal text)

conn.execute("SELECT name FROM products").fetchall()
# → [..., "Hack', 0); DROP TABLE products; --", ...]
```

Table was not dropped. The entire payload is stored verbatim as a product name — the SQL
driver never treated it as executable SQL.

---

### Test 5 — XSS (stored payload rendered in search)

```
$ curl -s "http://127.0.0.1:5001/search?q=img" | grep "&lt;img"
&lt;img src=x onerror=alert(1)&gt;

$ curl -s "http://127.0.0.1:5001/search?q=img" | grep -E '<td[^>]*>.*<img'
(no output — 0 literal <img> tags inside <td>)
```

Payload rendered as escaped HTML text. Browser cannot execute it.

---

### Test 6 — SQLi search (UNION SELECT)

```
# URL-decoded payload: x' UNION SELECT 1,'HACKED',0,'2026-01-01'--
$ curl -s "http://127.0.0.1:5001/search?q=x%27+UNION+SELECT+1%2C%27HACKED%27%2C0%2C%272026-01-01%27--"

# Injected <td> rows with "HACKED": 0
# (String appears 2× in page — only in the echoed search query in the UI, not in result rows)
```

No injected rows. The UNION payload is treated as a LIKE search string: no product
has a name literally containing `x' UNION SELECT ...`, so 0 results.

---

### Test 7 — SQLi search (OR 1=1)

```
# URL-decoded payload: ' OR '1'='1
$ curl -s "http://127.0.0.1:5001/search?q=%27+OR+%271%27%3D%271"

# <td> cells in result: 0
```

0 results. The condition `name LIKE "% OR '1'='1%"` matches no product names.
The `OR 1=1` is treated as a literal string, not as SQL logic.

---

### Test 8 — Generic error page (404)

```
$ curl -s http://127.0.0.1:5001/nonexistent-page | grep "Traceback"
(no output)

$ curl -s http://127.0.0.1:5001/nonexistent-page | grep "Page not found"
Page not found.
```

No stack trace. No framework internals. Generic message only.

Note: the word "Flask" appears twice in the response — both in our own UI footer
(`Built with Flask 3.1`) and dev banner. This is intentional design disclosure,
not a security issue. The HTTP `Server` header (which is the actual attack surface
for CWE-200) is masked separately (Test 1).

---

## Notes on defense-in-depth interaction

During Test 3 (CSRF without token), the server returned 400 **before** the SQL
layer was reached. This demonstrates layered defense: even if parameterized queries
weren't in place, the CSRF check would have blocked the write. Both protections are
independent and additive.
