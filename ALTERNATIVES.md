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

## D39: CI lint gate mode (informational vs blocking) -- CLOSED in Fase 1.5

- Chosen (Fase 1): ruff check runs in CI as a separate job, non-blocking (continue-on-error: true)
- Alternative: blocking gate from the start (fail the workflow on any ruff finding)
- Reason: first-ever ruff run on ~67 commits of pre-existing code surfaced 29 findings
  (mostly F401 unused imports in tests, a few F841/F811, plus F403/F405 on intentional
  settings star-imports). Blocking immediately would have required mixing a large mechanical
  cleanup into the CI/CD setup thread (Fase 1), violating Phase discipline (CLAUDE.md rule 5).
- Action (Fase 1): cleanup deferred to Fase 1.5 (lint cleanup), a short dedicated thread before Fase 2.
- Closure (Fase 1.5): all 29 findings resolved (22 auto-fixed F401, 3 manually-reviewed F841,
  3 explicit noqa for intentional F403/F405 settings star-imports). `ruff check .` reaches
  0 findings. Lint job promoted from continue-on-error:true to blocking, confirmed green in
  GitHub Actions. D39 is now closed -- no further action needed.

## D40: Internal-only docs (SESSION_STATE.md, POSTMORTEM.md, ALTERNATIVES.md) tracked in repo root

- Current: SESSION_STATE.md, POSTMORTEM.md, ALTERNATIVES.md live tracked
  in the repo root, with full commit history already in git.
- Alternative: move to .claude/local/ (gitignored), matching the pattern
  already used in other personal projects, keeping only public-facing
  docs (README.md, DEPLOY.md) in the repo root.
- Reason not to act now: this is a repo-architecture decision (what is
  public vs. internal), not enforcement or routing -- out of scope for
  Fase 2. Moving already-tracked files requires git rm --cached (history
  rewrite of tracking, not a gitignore-only change), a different risk
  category than the routing.local.md addition done in this phase.
- Action: deferred to Fase 6 (Arquitectura y cierre de portfolio), same
  thread where README/POSTMORTEM public-facing review already happens.
  To resolve together with the still-pending ROADMAP.md file-name
  reference fix in django-test.md/django-devops.md (also deferred).
