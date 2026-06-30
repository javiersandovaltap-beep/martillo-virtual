#!/usr/bin/env bash
# phase0_english.sh - Rewrite editable .md files in English (L01 compliance)
# and re-commit Phase 0 baseline.
#
# Run from project root (where manage.py is) in Git Bash.
# Prerequisites: Phase 0 already executed (commit 726780b exists).
#
# This script:
# 1. Rewrites SESSION_STATE.md, CLAUDE.md, AGENTS.md, ALTERNATIVES.md in English
# 2. Verifies ASCII pure on all 4 files
# 3. Resets git HEAD (keeps files on disk)
# 4. Re-commits baseline with English .md files
# 5. Re-tags v0.1-stable

set -e

# === Colors ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 0 v2: English .md files (L01)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# === Verify we are in project root ===
if [ ! -f manage.py ]; then
    echo -e "${RED}ERROR: manage.py not found${NC}"
    echo "Run this script from the project root."
    exit 1
fi

# === Verify .claude/agents/ exists (subagents already in English) ===
if [ ! -d .claude/agents ]; then
    echo -e "${RED}ERROR: .claude/agents/ not found${NC}"
    echo "Phase 0 must be executed first."
    exit 1
fi

echo -e "${YELLOW}--- Step 1: Rewrite SESSION_STATE.md in English ---${NC}"
cat > SESSION_STATE.md << 'PHASE0_EOF'
# SESSION_STATE.md - MartilloVirtual

> Source of truth for project state. Read before each session.
> Update after each commit. ASCII pure.

## Current state

- Phase: 0 (Recovery + Migrations Audit) - completed
- Last commit: chore: Fase 0 baseline (English .md files per L01)
- Last tag: v0.1-stable
- Blockers: none
- Next step: Phase 1 (Critical blockers + Security audit)

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

## Open questions

(none - all answered in Phase 0 batch)

## Bugs detected and status

| ID | Description | Phase | Status |
|----|-------------|-------|--------|
| B01 | ofertar() does not validate POST method | Phase 1 | pending |
| B02 | Race condition in ofertar() | Phase 1 | pending |
| B03 | N+1 in precio_actual/total_ofertas | Phase 3 | pending |
| B04 | N+1 in MisSubastasView | Phase 3 | pending |
| B05 | InicioView executes queryset 2x | Phase 3 | pending |
| B06 | form_oferta in context but not rendered | Phase 3 | pending |
| B07 | Open redirect in login_view | Phase 1 | pending |
| B08 | seed_data.py broken (ESTADO_ACTIVA) | Phase 0 | fixed |
| B09 | Logout without @require_POST | Phase 1 | pending |
| B10 | fecha_inicio and creado_en redundant | Phase 3 | pending |
| F01 | "En vivo" badge unconditional | Phase 3 | pending |
| F02 | Stats counter inconsistent with badge | Phase 3 | pending |
| F03 | Divider depends on field order | Phase 3 | pending |
| F04 | CSS @import duplicates HTML link | Phase 3 | pending |
| D01 | No index on Oferta.creado_en | Phase 3 | pending |
| D02 | No index on Subasta.estado, fecha_cierre | Phase 3 | pending |
| D04 | Migrations squashable | Phase 5 | pending |
| S01 | SECRET_KEY exposed in zip | Phase 0 | rotated |
| S02 | SECRET_KEY without graceful fallback | Phase 1 | pending |
| S03 | ALLOWED_HOSTS parsing fragile | Phase 1 | pending |
| S05 | Open redirect (see B07) | Phase 1 | pending |
| S06 | /admin/ exposed without protection | Phase 1 | confirmed Option A |
| S07 | No rate limiting in auth | Phase 4 | pending |
| S08 | README lies about CSP | Phase 5 | pending |
| S09 | No SECURE_PROXY_SSL_HEADER | Phase 1 | pending |
| S10 | HSTS 1 year without pre-commit warn | Phase 1 | pending |
| C01 | requirements vs venv mismatch | Phase 0 | fixed |
| C02 | martillo_v3/ stale | Phase 0 | removed |
| C04 | No git init | Phase 0 | fixed |
| C06 | No tests | Phase 4 | pending |
| C08 | ManifestStaticFilesStorage in dev | Phase 2 | pending |
PHASE0_EOF
echo -e "${GREEN}[OK] SESSION_STATE.md rewritten in English${NC}"

echo -e "${YELLOW}--- Step 2: Rewrite CLAUDE.md in English ---${NC}"
cat > CLAUDE.md << 'PHASE0_EOF'
# CLAUDE.md - MartilloVirtual

> Operational rules for Claude Code in this project.
> Claude Code is the executor. The senior chat plans and reviews.
> ASCII pure.

## Project context

- Project: MartilloVirtual (online auction house)
- Stack: Django 6.0.3, Python 3.12+, SQLite (dev), Supabase Postgres (prod)
- Deploy: Render free tier (Procfile, no Docker)
- Main app: subastas (models: Subasta, Oferta)
- Settings: config/settings/{base,development,production}.py
- Frontend language: Spanish (UI text in templates). Operational .md files in English (L01).

## Hard rules (17)

1. Do not assume anything about the project without evidence
2. Do not propose diffs without evidence
3. ASCII pure in editable .md files (SESSION_STATE.md, CLAUDE.md, AGENTS.md, ALTERNATIVES.md)
4. Exception: .py files can have emojis in assertions
5. One change per commit, conventional commits
6. Tag vX.Y-stable when closing each phase
7. If a hypothesis fails 2 times, forbidden to repropose. Request new evidence
8. 3-layer validation Django before each commit that touches code
9. Byte-level verification when in doubt
10. Do not trust verbal reports - request bytes (curl.exe, Get-Content -Encoding UTF8, git diff)
11. Lesson learned in SESSION_STATE.md in real-time, not batched
12. False alarms acknowledged with "I withdraw the alert"
13. Security audit mandatory in Phase 1
14. Migrations audited before applying (showmigrations + migrate --plan)
15. Settings split dev/prod (already done in Phase 0)
16. Attached plan is AUDITED, not executed as-is
17. Dockerfile designed in Phase 5, not before

## Django layer validation

| Layer | Command | When to use |
|-------|---------|-------------|
| 1 | python manage.py check | Before commit touching settings/apps/models |
| 2a | python manage.py makemigrations --check --dry-run | Before commit touching models.py |
| 2b | python manage.py test | Before commit touching views/models/forms |
| 3 | python manage.py runserver + curl.exe | Before commit touching views/urls/templates |

Hard rule: do NOT mix layers. If Layer 1 fails, do not attempt Layer 3 until Layer 1 is fixed.

## Conventional commits

- fix(BXX): bug fix (B = bug ID from SESSION_STATE.md)
- feat(BXX): new feature
- refactor(BXX): refactor without behavior change
- docs: documentation
- chore: mechanical tasks
- test(BXX): tests
- security(BXX): security fixes

## Model routing (5 task types)

| Task type | Claude Code slot | Real model | Justification |
|-----------|------------------|------------|---------------|
| Operational docs | sonnet | Nemotron | Mechanical + L13 cross-check |
| Django tests | opus | Minimax M2.7 | Reasoning on views/models/forms |
| HTML templates | haiku | GLM-5.1 | Mechanical + compare style |
| DB migrations | opus | Minimax M2.7 | Schema/data reasoning |
| View refactors | opus | Minimax M2.7 | Django patterns (CBV/FBV/service) |
| Security audit | opus | Minimax M2.7 | Attack vectors |
| Settings split | bash script | N/A | Mechanical |
| Deploy artifacts | opus | Minimax M2.7 | Build size, layers, gunicorn |

## Subagents (.claude/agents/)

Claude Code invokes subagents automatically based on task type:

- django-backend: views, models, forms, urls, admin, management commands, migrations
- django-frontend: templates, static, CSS, JS vanilla
- django-test: Django tests, coverage, fixtures
- django-security: audit, hardening, OWASP
- django-devops: Dockerfile, render.yaml, Procfile, deploy
- django-docs: README, POSTMORTEM, SESSION_STATE.md updates

## When to delegate to subagent

- Frontend changes (templates, CSS, JS) -> django-frontend
- Backend changes (views, models, forms) -> django-backend
- Writing tests -> django-test
- Security audit -> django-security
- Deploy config (Dockerfile, render.yaml) -> django-devops
- Docs (README, AGENTS.md) -> django-docs

## Shell and encoding

- Claude Code uses Git Bash (not PowerShell) on Windows
- Set PYTHONIOENCODING=utf-8 in bash scripts that run python
- For Windows paths in Python: use cygpath -m to convert /c/Users/... to C:/Users/...
- curl.exe (not curl alone) for HTTP validation on Windows

## Django anti-patterns to avoid

- N+1 queries: properties that call .count() or .first() per instance. Use annotate()
- Open redirects: validate next with url_has_allowed_host_and_scheme
- Race conditions: wrap multi-step writes in transaction.atomic + select_for_update
- SECRET_KEY in code: always from os.environ
- DEBUG=True in production: never
- Raw SQL: use ORM, never .raw() or .extra() without explicit approval
- mark_safe: avoid it, Django auto-escapes by default

## Updates to this file

Any change to CLAUDE.md must:
1. Be approved by the senior chat
2. Maintain ASCII pure
3. Update SESSION_STATE.md with the decision
PHASE0_EOF
echo -e "${GREEN}[OK] CLAUDE.md rewritten in English${NC}"

echo -e "${YELLOW}--- Step 3: Rewrite AGENTS.md in English ---${NC}"
cat > AGENTS.md << 'PHASE0_EOF'
# AGENTS.md - MartilloVirtual

> Agent architecture for this project.
> Defines how tasks are delegated among multiple agents.
> ASCII pure.

## 3 agent layers

### Layer 1 - Orchestration (senior chat)

The senior chat acts as architect + reviewer:
- Plans: designs prompts for Claude Code, decides task order
- Assigns: LLM routing + appropriate subagent per task
- Reviews: validates output with criteria, byte-level when in doubt
- Decides: approves, rejects, requests corrections
- Acknowledges false alarms with "I withdraw the alert"

Senior chat tools:
- Task tool with subagent_type=general-purpose (cross-validation)
- Task tool with subagent_type=Plan (implementation design)
- Task tool with subagent_type=Explore (quick codebase exploration)

### Layer 2 - Execution (Claude Code subagents)

6 subagents in .claude/agents/. Claude Code invokes them automatically
based on the description field in the frontmatter.

| Agent | Scope | Tools | LLM routing |
|-------|-------|-------|-------------|
| django-backend | views, models, forms, urls, admin, management commands, migrations | Read, Edit, Write, Bash, Grep, Glob | opus/Minimax or sonnet/Nemotron |
| django-frontend | templates, static, CSS, JS vanilla | Read, Edit, Write, Bash, Grep, Glob | haiku/GLM-5.1 or sonnet/Nemotron |
| django-test | Django tests, coverage, fixtures | Read, Edit, Write, Bash, Grep, Glob | opus/Minimax |
| django-security | audit, hardening, OWASP | Read, Edit, Write, Bash, Grep, Glob | opus/Minimax |
| django-devops | Dockerfile, render.yaml, Procfile, deploy | Read, Edit, Write, Bash, Grep, Glob | opus/Minimax |
| django-docs | README, POSTMORTEM, SESSION_STATE.md | Read, Edit, Write, Bash, Grep, Glob | sonnet/Nemotron |

Each agent defines:
- Specific role
- File scope (what it can touch)
- Allowed tools
- Validation rules (3-layer Django)
- When to delegate to another agent
- Anti-patterns to avoid

### Layer 3 - Review (senior chat + shell script)

- Senior chat reviews Claude Code output with specific criteria per bug
- Git Bash shell script (scripts/run_tests.sh) corroborates tests independently
- If results match: approve
- If not: investigate discrepancy byte-level
- Byte-level verification when in doubt about encoding, hashes, or verbal reports

## Communication protocol

1. Senior chat designs prompt for Claude Code (Phase N, bug X)
   - Specifies required evidence (file:line, validation command)
   - Defines approval criteria (checklist)
   - Assigns subagent + LLM routing

2. User pastes prompt in Claude Code

3. Claude Code invokes appropriate subagent (or executes directly)
   - Subagent executes edit
   - Subagent runs Layer 1: python manage.py check
   - Subagent runs Layer 2a: makemigrations --check --dry-run (if touches models)
   - Subagent runs Layer 2b: python manage.py test (if touches views/models/forms)
   - Subagent runs Layer 3: runserver + curl.exe (if touches views/urls/templates)
   - Subagent commits with conventional commit

4. User pastes raw output to senior chat
   - Do NOT trust verbal reports from Claude Code
   - For byte-level validation: curl.exe -o file + Get-Content -Encoding UTF8

5. Senior chat reviews with criteria
   - If approved: next task
   - If not approved: asks Claude Code to correct WITHOUT user generating diff
   - If hypothesis fails 2 times: forbidden to repropose, request new evidence
   - False alarms: "I withdraw the alert"

6. Lesson learned is documented in SESSION_STATE.md in real-time (L21+)

## Orthogonality: LLM routing vs subagents

The LLM routing (opus/sonnet/haiku -> Minimax/Nemotron/GLM-5.1) is ORTHOGONAL to subagents.
A django-backend subagent can run with any model depending on the specific task.

- LLM routing is decided by TASK TYPE (tests, docs, migrations, etc.)
- Subagent is decided by DOMAIN (backend, frontend, security, etc.)

Example: "refactor ofertar() to service layer"
- Subagent: django-backend (backend domain)
- LLM routing: opus/Minimax (view refactor type)

Example: "test for ofertar()"
- Subagent: django-test (tests domain)
- LLM routing: opus/Minimax (Django tests type)

## 3-model experiment (5 task types)

Each task type is executed with 1-2 different models to compare:

1. Operational docs: 1 file per model
   - CLAUDE.md (Nemotron)
   - AGENTS.md (GLM-5.1)
   - ALTERNATIVES.md (Minimax)
   Comparison: clarity, completeness, rule adherence

2. Django tests: 1 file per model
   - tests_views.py (Minimax)
   - tests_models.py (Nemotron)
   - tests_forms.py (GLM-5.1)
   Comparison: coverage, assertion quality, fixture handling

3. HTML templates: 1 file per model
   - subasta_detail.html refactor (GLM-5.1)
   - subasta_form.html refactor (Nemotron)
   - mis_subastas.html refactor (Minimax)
   Comparison: Django template syntax, accessibility, UX

4. DB migrations: 1 file per model
   - 0003_indexes.py (Minimax)
   - 0004_squash.py (Nemotron)
   - 0005_ganador_fk.py (GLM-5.1)
   Comparison: dependencies, data loss risk, reversibility

5. View refactors: 1 file per model
   - ofertar -> service layer (Minimax)
   - login_view -> LoginView CBV (Nemotron)
   - registro -> SignUpView CBV (GLM-5.1)
   Comparison: Django patterns, readability, testability

Comparison is documented in POSTMORTEM.md at the end (Phase 5).

## Updates to this file

Any change to AGENTS.md must:
1. Be approved by the senior chat
2. Maintain ASCII pure
3. Update SESSION_STATE.md with the decision
PHASE0_EOF
echo -e "${GREEN}[OK] AGENTS.md rewritten in English${NC}"

echo -e "${YELLOW}--- Step 4: Rewrite ALTERNATIVES.md in English ---${NC}"
cat > ALTERNATIVES.md << 'PHASE0_EOF'
# ALTERNATIVES.md - MartilloVirtual

> Design decisions and alternatives considered.
> Each decision has: chosen option, alternative, reason, action.
> ASCII pure.

## D01: SQLite in dev vs PostgreSQL in dev

- Chosen: SQLite in dev (Django default)
- Alternative: PostgreSQL in dev via docker-compose
- Reason: simplicity, project already has working SQLite, no real data
- Action: none

## D02: CBV vs FBV

- Chosen: mixed. CBVs for CRUD (LoginRequiredMixin, UserPassesTestMixin), FBVs for auth and ofertar
- Alternative: all CBV
- Reason: auth with CBV requires custom SignupView, ofertar is procedural logic with race condition
- Action: refactor ofertar to service layer in Phase 3 (still FBV but extracts logic)

## D03: crispy_forms vs custom CSS

- Chosen: custom CSS (already implemented in style.css, 268 lines with OKLCH design system)
- Alternative: enable crispy_forms (already in requirements.txt and INSTALLED_APPS)
- Reason: custom CSS already works and looks professional, crispy duplicates work
- Action: remove crispy_forms and crispy_bootstrap5 from requirements.txt and INSTALLED_APPS in Phase 2

## D04: STATICFILES_STORAGE in dev

- Chosen: conditional
  - dev: whitenoise.storage.CompressedStaticFilesStorage (no Manifest)
  - prod: whitenoise.storage.CompressedManifestStaticFilesStorage
- Alternative: Manifest in both
- Reason: Manifest requires prior collectstatic, friction in dev
- Action: implement conditional in base.py in Phase 2

## D05: Admin URL

- Chosen: standard /admin/ (confirmed by user in Phase 1)
- Alternative: rename to /admin-panel-xyz/ or restrict by IP middleware
- Reason: portfolio, /admin/ standard is OK with rate limiting + strong superuser
- Action: confirmed Option A in Phase 1

## D06: Dockerfile

- Chosen: create in Phase 5 as learning exercise, NOT use for deploy
- Alternative: deploy via Dockerfile
- Reason: Render free tier does NOT support Docker, Procfile is sufficient. User wants to learn Docker.
- Action: Dockerfile + README explaining local build, not used in deploy

## D07: Supabase vs alternative

- Chosen: Supabase (managed postgres, free tier)
- Alternative: Render PostgreSQL, Neon, Railway
- Reason: Supabase has generous free tier (500MB, 5 connections), user already has account
- Action: create new project in Phase 5 (user deleted previous to free space)

## D08: Tests with Django TestCase vs pytest-django

- Chosen: pytest-django (to confirm in Phase 4)
- Alternative: Django TestCase (built-in, no extra deps)
- Reason: pytest-django is de facto standard in 2026, fixtures, parametrize, better output
- Action: add pytest + pytest-django + coverage to requirements in Phase 4

## D09: Rate limiting

- Chosen: django-ratelimit (simple decorator)
- Alternative: django-axes (more complete, IP blocking)
- Reason: django-ratelimit is enough for portfolio, lighter
- Action: add django-ratelimit to requirements in Phase 4

## D10: Automatic subasta closing

- Chosen: management command + cron in Render
- Alternative: celery beat, django-cron, post_save signal
- Reason: celery is overkill for portfolio, signal does not scale to existing subastas
- Action: create cerrar_subastas command in Phase 3 + cron in Render in Phase 5

## D11: DB scalability

- Chosen: Supabase free tier (5 connections, 500MB)
- Alternative: Supabase paid, Neon, pgBouncer pooler
- Reason: portfolio, free tier enough for demo
- Action: if app grows, migrate to paid or pooler in future

## D12: Background tasks

- Chosen: NOT implement (despite README mentioning it)
- Alternative: Django 6.0 Background Tasks framework
- Reason: overkill for portfolio, winner email done synchronously or via cron
- Action: remove Background Tasks mention from README in Phase 5

## D13: Native Django 6.0 CSP

- Chosen: evaluate in Phase 4 (post-tests)
- Alternative: django-csp external library
- Reason: Django 6.0 has native CSPMiddleware, but requires careful config (nonces for inline JS)
- Action: if enabled, move inline JS to external .js files or use nonces

## D14: Template partials (partialdef)

- Chosen: NOT implement (despite README mentioning it)
- Alternative: use partialdef for reusable navbar
- Reason: navbar is already simple, partialdef adds complexity without clear benefit
- Action: remove partialdef mention from README in Phase 5

## D15: HSTS duration

- Chosen: start with 300 seconds (5 min) in Phase 1, raise to 31536000 (1 year) in Phase 5
- Alternative: 1 year from the start
- Reason: 1-year HSTS is irreversible for 1 year in browsers that visit. Start short to validate.
- Action: SECURE_HSTS_SECONDS = 300 in Phase 1, raise in Phase 5 post-successful deploy

## D16: Git Hooks

- Chosen: NOT implement (for now)
- Alternative: pre-commit hook that runs check + test
- Reason: friction in dev, prefer explicit validation via 3-layer
- Action: reconsider in Phase 4 if tests are fast

## D17: Language for operational .md files

- Chosen: English for all .md editable by Claude Code (L01 compliance)
- Alternative: Spanish (more readable for user)
- Reason: token efficiency (English tokens are shorter in LLMs), Claude trained primarily on English, consistency with prompts
- Action: Phase 0 baseline re-committed with English .md files. README, DEPLOY.md, POSTMORTEM.md remain in Spanish (human consumption).
PHASE0_EOF
echo -e "${GREEN}[OK] ALTERNATIVES.md rewritten in English${NC}"

echo ""

# === Step 5: ASCII verification ===
echo -e "${YELLOW}--- Step 5: ASCII pure verification ---${NC}"
python -c "
import sys
files = ['SESSION_STATE.md', 'CLAUDE.md', 'AGENTS.md', 'ALTERNATIVES.md']
all_ok = True
for f in files:
    with open(f, 'rb') as fh:
        content = fh.read()
    non_ascii = [b for b in content if b > 127]
    if non_ascii:
        print(f'  {f}: FAIL - {len(non_ascii)} non-ASCII bytes')
        # Show first 3 non-ASCII bytes
        for i, b in enumerate(non_ascii[:3]):
            print(f'    byte {i}: 0x{b:02x}')
        all_ok = False
    else:
        size = len(content)
        print(f'  {f}: OK - ASCII pure ({size} bytes)')
if not all_ok:
    sys.exit(1)
print('All 4 files are ASCII pure.')
"
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: ASCII verification failed${NC}"
    exit 1
fi
echo ""

# === Step 6: Verify L21 is in SESSION_STATE.md ===
echo -e "${YELLOW}--- Step 6: Verify L21 in SESSION_STATE.md ---${NC}"
if grep -q "L21:" SESSION_STATE.md; then
    echo -e "${GREEN}[OK] L21 found in SESSION_STATE.md${NC}"
else
    echo -e "${RED}ERROR: L21 not found in SESSION_STATE.md${NC}"
    exit 1
fi
echo ""

# === Step 7: Git reset ===
echo -e "${YELLOW}--- Step 7: Git reset (keep files on disk) ---${NC}"

# Show current state
echo "Current git log:"
git log --oneline -5 2>&1 || echo "(no commits yet)"
echo ""

# Delete HEAD ref (resets to no commits, keeps working tree)
git update-ref -d HEAD 2>/dev/null || true
git restore --staged . 2>/dev/null || true

echo "After reset:"
git log --oneline -5 2>&1 || echo "(no commits)"
echo ""

# === Step 8: Re-add and re-commit ===
echo -e "${YELLOW}--- Step 8: Re-commit baseline with English .md ---${NC}"

git add .

git commit -m "chore: Fase 0 baseline (English .md files per L01)

- Removed martillo_v3/ (stale snapshot)
- Fixed requirements.txt: psycopg 3.2.4 -> 3.3.3
- Fixed seed_data.py: Subasta.ESTADO_ACTIVA -> Subasta.Estado.ACTIVA
- Created new venv (Python 3.14.5)
- Generated new SECRET_KEY in .env (rotated, previous exposed in zip)
- Reset db.sqlite3, applied 20 migrations
- Seed data: 6 subastas, 1 user don_roberto
- Created superuser: JavAdmin
- Operational files in English (L01): SESSION_STATE.md, CLAUDE.md, AGENTS.md, ALTERNATIVES.md
- Subagents: .claude/agents/*.md (6 agents in English)
- L21 documented: git show --stat artifact

Tag: v0.1-stable"

echo ""

# === Step 9: Re-tag ===
echo -e "${YELLOW}--- Step 9: Re-tag v0.1-stable ---${NC}"
git tag -f v0.1-stable
echo -e "${GREEN}[OK] tag v0.1-stable recreated${NC}"
echo ""

# === Final verification ===
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 0 v2 completed${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "=== Final git log ==="
git log --oneline -5
echo ""

echo "=== git tags ==="
git tag
echo ""

echo "=== Tree file count (should be 51) ==="
git ls-tree -r HEAD --name-only | wc -l
echo ""

echo "=== Tree duplicates check (should be empty) ==="
git ls-tree -r HEAD --name-only | sort | uniq -c | awk '$1 > 1'
echo "(empty = OK)"
echo ""

echo "=== ASCII pure re-verify ==="
python -c "
files = ['SESSION_STATE.md', 'CLAUDE.md', 'AGENTS.md', 'ALTERNATIVES.md']
for f in files:
    with open(f, 'rb') as fh:
        content = fh.read()
    non_ascii = [b for b in content if b > 127]
    status = 'FAIL' if non_ascii else 'OK'
    print(f'  {f}: {status}')
"
echo ""

echo "=== L21 verify ==="
grep "L21:" SESSION_STATE.md
echo ""

echo "=== .claude/agents/ (already in English) ==="
ls .claude/agents/
echo ""

echo -e "${GREEN}Phase 0 v2 complete. Ready for Prompt 1 (settings fixes).${NC}"
