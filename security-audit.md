# Security Audit — Mapping to White-Hat Secure Development Reference

> This document maps the requirements of the White-Hat secure development
> reference document (originally in Hebrew, "פרמטרים לפיתוח מאובטח")
> to the current state of this codebase.
>
> Updated at every step. Final audit at step 8.

---

## Reference document — translated requirements

The reference defines the following application-level requirements:

1. **System audience identification** (external customers, employees, suppliers)
2. **Data sensitivity classification**
3. **Input validation**
   - Whitelist by default
   - Blacklist only when no other choice
   - Logical / range checks
   - Permission check before any action
4. **Application user permissions vs database**
   - Minimal privileges
   - Credentials stored server-side only, encrypted (e.g. AES-256)
5. **Database queries**
   - No dynamic concatenated queries
   - Parameterized queries OR stored procedures
6. **Interface security**
   - Channel encryption (TLS)
   - Authentication mechanism

---

## Current code audit (as of step 6)

| # | Requirement | Implementation in this repo | Status | Action |
|---|---|---|---|---|
| 1 | Audience identified | Public app, no authentication (per challenge scope). Documented as out-of-scope. | OK (N/A documented) | Mention in interview: production app would define roles. |
| 2 | Data sensitivity classified | Public catalog data only — no PII, no payment data, no credentials. | OK (N/A documented) | — |
| 3a | Whitelist by default | DB level: `CHECK (length(name) > 0 AND length(name) <= 200)` and `CHECK (price >= 0)`. Flask level: `validate_name()` rejects empty/overlong names; `validate_price()` rejects non-numeric and negative values. FIXED in step 6 (commit 0ad0694). | OK (both layers) | — |
| 3b | Blacklist only when forced | Not used. | OK (compliant by absence) | — |
| 3c | Range / logical checks | DB enforces `price >= 0` and `length(name) BETWEEN 1 AND 200`. Flask mirrors: `len(name) > 200` rejected, `value < 0` rejected. FIXED in step 6. | OK (both layers) | — |
| 3d | Permission check before action | No authenticated users in scope. | OK (N/A documented) | Mention in interview. |
| 4a | Minimal DB user privileges | SQLite is file-based and single-user — no concept of DB user. | OK (N/A by design) | Mention in interview that on PostgreSQL/MySQL we would use a dedicated user with `GRANT INSERT, SELECT` only — never `DROP`, `ALTER`. |
| 4b | Encrypted credentials (AES-256) | Not applicable: SQLite has no DB credentials. | OK (N/A by design) | Mention in interview. |
| 5 | Parameterized queries | FIXED in step 6 (commit 4efd292). INSERT uses `execute("INSERT ... VALUES (?, ?)", (name, price))`. SEARCH uses `execute("... LIKE ?", (f"%{q}%",))`. Verified: DROP TABLE payload treated as literal string; OR 1=1 returns 0 rows; UNION SELECT injects nothing.: `f"INSERT INTO products (name, price) VALUES ('{name}', {price})"` executed via `executescript()`. Demonstrated to drop the `products` table with payload `Hack', 0); DROP TABLE products; --`. | EXPOSED (step 4) — TO DO (step 6) | Step 6.1: replace with `execute("INSERT ... VALUES (?, ?)", (name, price))`. |
| 5b | Stored XSS protection | FIXED in step 6 (commit 0ad0694). `\| safe` removed from `search.html`. Jinja2 auto-escape converts `<img onerror=...>` to `&lt;img onerror=...&gt;`. Server-side `validate_name()` adds an additional whitelist layer. Verified: XSS payload stored in step 4 is now rendered inert. | FIXED | — |
| 5c | CSRF protection | FIXED in step 6 (commit 067ca33). Flask-WTF `CSRFProtect(app)` enabled. `insert.html` includes `{{ csrf_token() }}` hidden field. POST without valid token → HTTP 400. Verified via curl: cross-origin POST rejected before reaching SQL layer. | FIXED | — |
| 5d | Generic error messages | FIXED in step 6 (commit 39988d7). `sqlite3.Error` is caught in both `/insert` and `/search`. Real error is passed to `logger.error()` (server-side only). Client receives generic string: `"An error occurred. Please try again."` Custom `@app.errorhandler(400/404/500)` returns `error.html` with no stack trace. | FIXED | — |
| 6a | TLS / HTTPS channel | Flask dev server runs HTTP on 127.0.0.1:5001. Not configured for HTTPS. | Deferred | Document in step 6 (Security Misconfiguration) and final README. Production deployment would terminate TLS at a reverse proxy (nginx/Cloudflare) or use `gunicorn` + cert. |
| 6b | Authentication mechanism | No authentication in scope. | OK (N/A documented) | Mention in interview. |
| 7  | Server header information disclosure (added at step 3) | FIXED in step 6 (commit 39988d7). Two-layer fix: (1) `WSGIRequestHandler.server_version = "Web Server"` and `version_string = lambda self: "Web Server"` overrides Werkzeug's connection-level header; (2) `@after_request` sets `response.headers["Server"] = "Web Server"` for app-level responses. Verified with `curl -i`: header now reads `Server: Web Server`. | FIXED | — |
| 8  | Werkzeug interactive debugger (added at step 3) | FIXED in step 6 (commit 39988d7). `debug` mode now controlled by environment: `is_production = os.environ.get("FLASK_ENV") == "production"`, then `app.run(debug=not is_production)`. Running with `FLASK_ENV=production` disables debug, removes RCE risk. Dev default remains `debug=True` on loopback only (127.0.0.1). | OK (env-controlled) | Set `FLASK_ENV=production` before any non-local deployment. |

---

## Summary

| Status | Count | Items |
|---|---|---|
| OK / FIXED (compliant or N/A documented) | 14 | 1, 2, 3a, 3b, 3c, 3d, 4a, 4b, 5 (SQLi), 5b (XSS), 5c (CSRF), 5d (info disclosure), 6b, 7 (Server header), 8 (env-controlled) |
| Deferred (production-only) | 1 | 6a (TLS) |
| Non-compliant | 0 | — |

---

## Defense in depth — beyond the reference

The reference document does not explicitly mention DB-level `CHECK`
constraints. This codebase adds them anyway as a deliberate
defense-in-depth measure:

- If Flask-side validation is bypassed (bug, future direct DB access,
  partial injection that survives parameterization), the database itself
  refuses to insert invalid rows.
- This was verified by attempting deliberately invalid INSERTs:
  - `price = -1` → blocked by `CHECK (price >= 0)`
  - `name = ''` → blocked by `CHECK (length(name) > 0 ...)`
  - `name` of 201 chars → blocked by `CHECK (... length(name) <= 200)`
  - `name = NULL` → blocked by `NOT NULL`

This goes beyond the literal requirement of the reference document.

---

## Items to highlight in interview

When asked "did you follow the secure development guidelines?", answer:

> "Yes — I mapped my code against the reference document and produced
> a written audit (`security-audit.md`). As of step 6, 14 of 15 items
> are fully compliant or N/A documented. The single deferred item (TLS)
> is intentionally out-of-scope for a local dev app and documented in
> the README — production deployment would terminate TLS at nginx or
> Cloudflare. The 4 central vulns (SQLi, XSS, CSRF, info disclosure)
> were first deliberately demonstrated on a vulnerable version, then
> fixed with separate atomic commits — so the protection is proven,
> not just assumed. I also added defense-in-depth beyond the reference
> (DB CHECK constraints, CSP header, X-Frame-Options, Server header
> masking, environment-controlled debug mode)."

This shows:
- You read their document.
- You understand each requirement, including which are N/A and why.
- You can defend every gap with a clear reason.
- You added defense-in-depth beyond the minimum.

---

## Items deliberately left as future work (out of scope)

These are mentioned for completeness — they would matter for a
production deployment but are out of scope for this take-home:

- **Rate limiting** (Flask-Limiter) — to mitigate volumetric DoS.
- **Dependency lockfile with hashes** (`pip-compile`, `uv`) — to mitigate
  supply-chain attacks where a PyPI package is compromised.
- **Structured logging + SIEM integration** — to detect attacks in real time.
- **Web Application Firewall (WAF)** — frontline filtering of common
  attack patterns.
- **Fail2ban / IP reputation** — to slow down brute-force / scraping.
- **Secrets management** (HashiCorp Vault, AWS Secrets Manager) — to
  store any future credentials outside of the codebase.

These are the kinds of items a senior pentester will probe for. Knowing
them by name and being able to explain when they apply is what
separates a junior from an interview-ready candidate.
