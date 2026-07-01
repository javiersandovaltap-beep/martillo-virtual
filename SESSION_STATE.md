# SESSION_STATE.md - MartilloVirtual

> Source of truth for project state. Read before each session.
> Update after each commit. ASCII pure.

## Current state

- Phase: 2 (Workflow discipline + Config split) - completed
- Last commit: docs: update SESSION_STATE.md for Phase 2 closure
- Last tag: v0.3-stable (pending)
- Blockers: none
- Next step: Phase 3 (Estabilizacion: N+1, UX consistency, indexes, subasta closing)

## Project context

- Project: MartilloVirtual (online auction house)
- Stack: Django 6.0.3, Python 3.12+, SQLite (dev), Supabase Postgres (prod)
- Deploy target: Render (free tier, Procfile, no Docker)
- Definition of done: portfolio ready for GitHub, locally tested, scalable
- DB: no real data, resettable
- Frontend language: Spanish (UI text, templates); operational .md files in English (L01)

## Phase history

### Phase 0 - Recovery + Migrations Audit (v0.1-stable)
- Removed martillo_v3/ (stale snapshot)
- Fixed requirements.txt: psycopg 3.2.4 -> 3.3.3
- Fixed seed_data.py: Subasta.ESTADO_ACTIVA -> Subasta.Estado.ACTIVA
- Created new venv (Python 3.14.5)
- Generated new SECRET_KEY in .env (rotated, previous was exposed in zip)
- Reset db.sqlite3, applied 20 migrations
- Seed data: 6 subastas, 1 user don_roberto
- Created superuser: JavAdmin
- Created operational files in English (L01): SESSION_STATE.md, CLAUDE.md, AGENTS.md, ALTERNATIVES.md
- Created subagents: .claude/agents/*.md (6 agents in English)
- git init + baseline commit + tag v0.1-stable

### Phase 1 - Critical blockers + Security audit (v0.2-stable)
- security(S02): SECRET_KEY con fallback graceful a ImproperlyConfigured (3034df4)
- security(S03): ALLOWED_HOSTS parsing filtra strings vacios (e27b513)
- security(S09): SECURE_PROXY_SSL_HEADER para reverse proxy de Render (b21268b)
- security(S10): HSTS 300s inicial, subir a 1 ano en Fase 5 (0afa99f)
- security(B07): fix open redirect in login_view with url_has_allowed_host_and_scheme (8bf3758) - verified with 5/5 attack vector tests
- fix(B08): add @require_POST to ofertar view (3a24ec2) - verified with 3/3 method validation tests
- fix(B09): add @require_POST to logout_view, remove internal method check (2c962cb) - verified with 4/4 method validation tests
- fix(B02): wrap ofertar in transaction.atomic + select_for_update (eb45817) - verified with 2/2 race condition tests
- docs: L22 (NIM timeout recovery), L23 (Layer 1 does not validate security), L24 (Git Bash + Windows native commands), L25 (Django test client HTTP_HOST)

### Phase 2 - Workflow discipline + Config split (v0.3-stable)
- fix(C08): STATICFILES_STORAGE conditional dev vs prod (e3fabee) - dev=Compressed, prod=CompressedManifest
- refactor(D03): remove unused crispy_forms dependencies (2c01960) - deps + INSTALLED_APPS + settings cleaned
- chore: remove dead import reverse from views.py (d3f791a) - leftover from B07 fix
- chore: add trailing newline to production.py (3ab3eca) - POSIX compliance
- docs(C07): expand .env.example with all env vars and comments (8505173) - comments + 5 KEY=value assignments
- No new lessons (mechanical phase)



## Lessons

### Inherited from proyecto2_scraper_api (L01-L10)

- L01: Invoke-WebRequest in PS 5.1 lies about encoding. Use curl.exe
- L02: BS4 ignores from_encoding with Unicode markup
- L03: uvicorn is rarely in PATH. Use python -m uvicorn
- L04: In-memory cache only clears by restarting process
- L05: Select-String 'import <pkg>' is NOT enough to declare a dep unused
- L06: Claude Code uses Git Bash, not PowerShell. cat/grep/sed native, taskkill //PID for Windows processes
- L07: Before Add-Content, verify with Select-String if content already exists
- L08: Claude Code can corrupt UTF-8 in .md with non-ASCII. Scan byte-level post-edit
- L09: Verbal reports from Claude Code about command outputs can be reconstructions. Always request curl.exe -o file + Get-Content -Encoding UTF8
- L10: Byte-pattern mojibake checks have false positives in files that intentionally contain mojibake strings. Apply check to diff, not full file

### Inherited from proyecto3_telegram_bot (L01-L20)

- L01: All prompts to Claude Code and editable .md files in English (token efficiency). README can be Spanish
- L02: Timeouts of Minimax M2.7 via NIM under free API load are transitory, do not discard the model permanently
- L03: A timeout can leave partial work on disk + commits with lying messages + tags. Always verify FS + git state before assuming clean baseline
- L09: Phase 0 must verify dependencies (venv, pip install), not only git init + .gitignore
- L10: In bash, backticks inside python -c with double quotes cause unexpected EOF. Use heredoc with single-quoted delimiter
- L11: Python on Windows uses cp1252 as stdout encoding. Set PYTHONIOENCODING=utf-8 in bash scripts that run python
- L12: When a Python test runs from /tmp and needs to import project modules, set PYTHONPATH=.
- L13: Structural validation (sections present, ASCII pure) does NOT catch content hallucinations. Always cross-check facts
- L14: In bash, $(pwd) inside cd /tmp && python -c is evaluated AFTER cd. Capture PROJECT_ROOT before
- L15: Git Bash paths (/c/Users/...) are not understood by Python on Windows. Use cygpath -m to convert
- L16: Grep for absence of pattern can give false positives from docstrings/comments. Use specific patterns
- L17: with sqlite3.connect(...) as conn does NOT close the connection (only commit/rollback). Use @contextmanager with conn.close() in finally
- L18: datetime('now') of SQLite has 1-second resolution. Tests with timestamp ordering must set explicit timestamps
- L19: To mock sync functions in async tests, use MagicMock NOT AsyncMock (causes RuntimeWarning "coroutine never awaited")
- L20: The ASCII pure rule applies ONLY to .md editable by Claude Code. .py files can have emojis in assertions

### New from martillo_virtual (L21+)

- L21: git show --stat HEAD can show duplicated files in the diff (presentation artifact). The final tree has NO duplicates. Always validate with git ls-tree -r HEAD --name-only | sort | uniq -c | awk '$1 > 1' before assuming a broken commit
- L22: NIM (Minimax M2.7) can return 'Decode wall clock timeout after 600s' during complex tasks. Claude Code appears frozen for up to 10 minutes. A user nudge (e.g. 'Finish the task') can resume execution. The timeout is transitory (L02) and does not corrupt partial work. If it recurs, consider splitting the prompt into smaller subtasks.
- L23: Layer 1 (python manage.py check) does NOT validate security logic. A wrong security fix (e.g., allowed_hosts=None defeats url_has_allowed_host_and_scheme) can pass Layer 1. Always verify security fixes with actual attack vector tests (Layer 3 with malicious input, or dedicated security tests in Phase 4). Do not trust Layer 1 alone for security fixes.
- L24 (CORRECTED): Git Bash on Windows mangles Windows native command flags. /F and /PID in taskkill /F /PID N get converted to paths (C:/Program Files/Git/F). Two valid fixes: (1) MSYS_NO_PATHCONV=1 taskkill /F /PID N (env var + SINGLE slash, NOT double slash -- double slash passes //F literally which taskkill rejects), or (2) powershell 'Stop-Process -Id N -Force' (avoids path conversion entirely). The double-slash trick //F works for some Windows commands but NOT for taskkill.
- L25: Django test client uses 'testserver' as default HTTP_HOST. In dev settings with ALLOWED_HOSTS = ['localhost', '127.0.0.1'] (no 'testserver'), ALL test client requests fail with DisallowedHost 400 BEFORE reaching the view. False positive: test scripts that only check 'evil.com not in Location' will PASS even though the view never ran. Fix: use Client(HTTP_HOST='localhost') in test scripts, or add 'testserver' to ALLOWED_HOSTS in test settings. Specific case of L23 (Layer 1 doesn't validate security) applied to test infrastructure.
- L27: @property is a Python data descriptor and takes precedence over instance __dict__. Annotating a queryset with the SAME name as a property does NOT shadow the property -- the property is still called. To use annotations in list views while keeping properties for single-instance access, use different annotation names (e.g., _total_ofertas) and add hasattr(self, '_total_ofertas') checks at the start of properties to use the annotated value when available.
- L28: Filtering queries by substring ('COUNT' in sql and 'subastas_oferta' in sql) gives false positives when a main SELECT has COUNT subqueries embedded. Correct metric for N+1 detection: total query count before/after fix. If total drops from N to 2-3, the fix worked. To filter pure COUNT queries, use q['sql'].lstrip().upper().startswith('SELECT COUNT') which matches only queries that START with SELECT COUNT, not those with COUNT embedded.

## Decisions log

- D01: SQLite in dev (Django default), PostgreSQL only in prod via Supabase
- D02: CBV for CRUD, FBV for auth and ofertar (refactor ofertar to service layer in Phase 3)
- D03: Remove crispy_forms in Phase 2 (installed but unused, custom CSS already works)
- D04: STATICFILES_STORAGE conditional (dev=Compressed, prod=CompressedManifest)
- D05: Admin URL standard /admin/ (confirmed by user in Phase 1 - Option A)
- D06: Dockerfile as learning exercise in Phase 5, NOT for deploy (Render free does not support Docker)
- D07: Supabase for prod (create project in Phase 5)
- D08: Tests with pytest-django (to confirm in Phase 4)
- D09: Rate limiting with django-ratelimit in Phase 4
- D10: Automatic closing via management command + cron in Render (Phase 3)
- D17: English for all .md editable by Claude Code (L01). README, DEPLOY.md, POSTMORTEM.md remain in Spanish (human consumption).
- D18: crispy_forms removed (was installed but never used in templates, custom CSS handles styling)
- D19: .env.example keeps KEY=value assignments (not just comments) for copy-paste usability

## Open questions

(none - all answered in Phase 0 batch)

## Bugs detected and status

| ID | Description | Phase | Status |
|----|-------------|-------|--------|
| B01 | (merged into B08) | Phase 1 | closed |
| B02 | Race condition in ofertar() | Phase 1 | fixed (eb45817) |
| B03 | N+1 in precio_actual/total_ofertas | Phase 3 | pending |
| B04 | N+1 in MisSubastasView | Phase 3 | pending |
| B05 | InicioView executes queryset 2x | Phase 3 | pending |
| B06 | form_oferta in context but not rendered | Phase 3 | pending |
| B07 | Open redirect in login_view | Phase 1 | fixed (8bf3758) |
| B08 | seed_data.py broken (ESTADO_ACTIVA) | Phase 0 | fixed |
| B09 | Logout without @require_POST | Phase 1 | fixed (2c962cb) |
| B10 | fecha_inicio and creado_en redundant | Phase 3 | pending |
| F01 | "En vivo" badge unconditional | Phase 3 | pending |
| F02 | Stats counter inconsistent with badge | Phase 3 | pending |
| F03 | Divider depends on field order | Phase 3 | pending |
| F04 | CSS @import duplicates HTML link | Phase 3 | pending |
| D01 | No index on Oferta.creado_en | Phase 3 | pending |
| D02 | No index on Subasta.estado, fecha_cierre | Phase 3 | pending |
| D04 | Migrations squashable | Phase 5 | pending |
| S01 | SECRET_KEY exposed in zip | Phase 0 | rotated |
| S02 | SECRET_KEY without graceful fallback | Phase 1 | fixed (3034df4) |
| S03 | ALLOWED_HOSTS parsing fragile | Phase 1 | fixed (e27b513) |
| S05 | Open redirect (see B07) | Phase 1 | fixed (8bf3758) |
| S06 | /admin/ exposed without protection | Phase 1 | confirmed Option A (D05) |
| S07 | No rate limiting in auth | Phase 4 | pending |
| S08 | README lies about CSP | Phase 5 | pending |
| S09 | No SECURE_PROXY_SSL_HEADER | Phase 1 | fixed (b21268b) |
| S10 | HSTS 1 year without pre-commit warn | Phase 1 | fixed (0afa99f) |
| C01 | requirements vs venv mismatch | Phase 0 | fixed |
| C02 | martillo_v3/ stale | Phase 0 | removed |
| C04 | No git init | Phase 0 | fixed |
| C06 | No tests | Phase 4 | pending |
| C08 | ManifestStaticFilesStorage in dev | Phase 2 | fixed (e3fabee) |
