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
