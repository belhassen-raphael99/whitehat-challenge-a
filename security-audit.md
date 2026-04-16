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
| 5 | Parameterized queries | Not implemented yet — the project intentionally starts with vulnerable string-concatenated queries (steps 4-5) before the secure rewrite (step 6). | TO DO (step 6) | **Critical item.** Will be addressed in step 6.1 — first vulnerability to fix. |
| 6a | TLS / HTTPS channel | Flask dev server runs HTTP. Not configured for HTTPS. | Deferred | Document in step 6 (Security Misconfiguration) and final README. Production deployment would terminate TLS at a reverse proxy (nginx/Cloudflare) or use `gunicorn` + cert. |
| 6b | Authentication mechanism | No authentication in scope. | OK (N/A documented) | Mention in interview. |

---

## Summary

| Status | Count | Items |
|---|---|---|
| OK (compliant or N/A documented) | 7 | 1, 2, 3b, 3d, 4a, 4b, 6b |
| Partial (DB layer only, Flask layer pending) | 1 | 3a, 3c |
| TO DO (planned for step 6) | 1 | 5 (parameterized queries) |
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
