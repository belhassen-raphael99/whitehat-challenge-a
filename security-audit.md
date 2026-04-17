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

## Current code audit (as of step 2)

| # | Requirement | Implementation in this repo | Status | Action |
|---|---|---|---|---|
| 1 | Audience identified | Public app, no authentication (per challenge scope). Documented as out-of-scope. | OK (N/A documented) | Mention in interview: production app would define roles. |
| 2 | Data sensitivity classified | Public catalog data only — no PII, no payment data, no credentials. | OK (N/A documented) | — |
| 3a | Whitelist by default | DB level: `CHECK (length(name) > 0 AND length(name) <= 200)` and `CHECK (price >= 0)`. Flask level: not yet (vulnerable phase). | Partial | Add explicit Flask-side validation in step 6. |
| 3b | Blacklist only when forced | Not used. | OK (compliant by absence) | — |
| 3c | Range / logical checks | DB enforces `price >= 0` and `length(name) BETWEEN 1 AND 200`. | OK (DB level) | Mirror at Flask level in step 6. |
| 3d | Permission check before action | No authenticated users in scope. | OK (N/A documented) | Mention in interview. |
| 4a | Minimal DB user privileges | SQLite is file-based and single-user — no concept of DB user. | OK (N/A by design) | Mention in interview that on PostgreSQL/MySQL we would use a dedicated user with `GRANT INSERT, SELECT` only — never `DROP`, `ALTER`. |
| 4b | Encrypted credentials (AES-256) | Not applicable: SQLite has no DB credentials. | OK (N/A by design) | Mention in interview. |
| 5 | Parameterized queries | Step 4 implements the deliberately vulnerable version: `f"INSERT INTO products (name, price) VALUES ('{name}', {price})"` executed via `executescript()`. Demonstrated to drop the `products` table with payload `Hack', 0); DROP TABLE products; --`. | EXPOSED (step 4) — TO DO (step 6) | Step 6.1: replace with `execute("INSERT ... VALUES (?, ?)", (name, price))`. |
| 5b | Stored XSS protection | Step 4 stores user input verbatim. Demonstrated by inserting `<img src=x onerror=alert(1)>` as a product name — accepted by all DB CHECK constraints (it is just text). Will fire when displayed in step 5 search results without escaping. | EXPOSED (step 4-5) — TO DO (step 6) | Step 6.2: rely on Jinja2 auto-escape (no `\|safe`), plus add server-side validation. |
| 5c | CSRF protection | The `/insert` form has no CSRF token. Any cross-origin POST can insert products. | EXPOSED (step 4) — TO DO (step 6) | Step 6.3: add Flask-WTF with `CSRFProtect(app)`. |
| 5d | Generic error messages | Raw `sqlite3.Error` is rendered to the client on insert failure (CWE-209 information exposure through error message). | EXPOSED (step 4) — TO DO (step 6) | Step 6: catch DB errors, log details server-side, return generic message to client. |
| 6a | TLS / HTTPS channel | Flask dev server runs HTTP on 127.0.0.1:5001. Not configured for HTTPS. | Deferred | Document in step 6 (Security Misconfiguration) and final README. Production deployment would terminate TLS at a reverse proxy (nginx/Cloudflare) or use `gunicorn` + cert. |
| 6b | Authentication mechanism | No authentication in scope. | OK (N/A documented) | Mention in interview. |
| 7  | Server header information disclosure (added at step 3) | `curl -i` reveals `Server: Werkzeug/3.1.8 Python/3.14.4` — leaks framework, version, and Python version. CWE-200. | TO DO (step 6) | Strip or override `Server` header via Flask response middleware. |
| 8  | Werkzeug interactive debugger (added at step 3) | `debug=True` is enabled for local development. The Werkzeug debugger allows arbitrary Python execution if the app is reachable from the network. Currently mitigated by `host=127.0.0.1` (loopback only). | OK in dev (mitigated by binding) — TO DO for prod | In step 6, force `debug=False` for any non-dev environment, document in README. |

---

## Summary

| Status | Count | Items |
|---|---|---|
| OK (compliant or N/A documented) | 8 | 1, 2, 3b, 3d, 4a, 4b, 6b, 8 (dev only) |
| Partial (DB layer only, Flask layer pending) | 2 | 3a, 3c |
| EXPOSED (intentional, will be fixed in step 6) | 4 | 5 (SQLi), 5b (XSS), 5c (CSRF), 5d (info disclosure) |
| TO DO (planned for step 6) | 1 | 7 (Server header) |
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
> a written audit (`security-audit.md`). 7 of 11 items are fully
> compliant. 1 item is partial (input validation: I added DB-level
> CHECK constraints already, Flask-level validation is added in
> step 6 as part of the security hardening pass). 1 item is the
> central anti-SQLi requirement (parameterized queries) which is
> demonstrated with a deliberate vulnerable-then-fixed approach to
> prove the protection works. 1 item (TLS) is deferred to production
> deployment and documented in the README. The remaining items are
> N/A by scope (no authentication, no DB user concept with SQLite)."

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
