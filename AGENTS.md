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
| django-backend | views, models, forms, urls, admin, management commands, migrations | Read, Edit, Write, Bash, Grep, Glob | opus or sonnet |
| django-frontend | templates, static, CSS, JS vanilla | Read, Edit, Write, Bash, Grep, Glob | haiku or sonnet |
| django-test | Django tests, coverage, fixtures | Read, Edit, Write, Bash, Grep, Glob | opus |
| django-security | audit, hardening, OWASP | Read, Edit, Write, Bash, Grep, Glob | opus |
| django-devops | Dockerfile, render.yaml, Procfile, deploy | Read, Edit, Write, Bash, Grep, Glob | opus |
| django-docs | README, POSTMORTEM, SESSION_STATE.md | Read, Edit, Write, Bash, Grep, Glob | sonnet |

Real slot-to-model mapping lives in .claude/routing.local.md (gitignored,
not part of this repo).

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

The LLM routing (opus/sonnet/haiku) is ORTHOGONAL to subagents. Real model
mapping for each slot lives in .claude/routing.local.md (gitignored).
A django-backend subagent can run with any model depending on the specific task.

- LLM routing is decided by TASK TYPE (tests, docs, migrations, etc.)
- Subagent is decided by DOMAIN (backend, frontend, security, etc.)

Example: "refactor ofertar() to service layer"
- Subagent: django-backend (backend domain)
- LLM routing: opus (view refactor type)

Example: "test for ofertar()"
- Subagent: django-test (tests domain)
- LLM routing: opus (Django tests type)

## 3-model experiment (5 task types)

Each task type is executed with 1-2 different models to compare:

1. Operational docs: 1 file per model
   - CLAUDE.md (sonnet)
   - AGENTS.md (haiku)
   - ALTERNATIVES.md (opus)
   Comparison: clarity, completeness, rule adherence

2. Django tests: 1 file per model
   - tests_views.py (opus)
   - tests_models.py (sonnet)
   - tests_forms.py (haiku)
   Comparison: coverage, assertion quality, fixture handling

3. HTML templates: 1 file per model
   - subasta_detail.html refactor (haiku)
   - subasta_form.html refactor (sonnet)
   - mis_subastas.html refactor (opus)
   Comparison: Django template syntax, accessibility, UX

4. DB migrations: 1 file per model
   - 0003_indexes.py (opus)
   - 0004_squash.py (sonnet)
   - 0005_ganador_fk.py (haiku)
   Comparison: dependencies, data loss risk, reversibility

5. View refactors: 1 file per model
   - ofertar -> service layer (opus)
   - login_view -> LoginView CBV (sonnet)
   - registro -> SignUpView CBV (haiku)
   Comparison: Django patterns, readability, testability

Comparison is documented in POSTMORTEM.md at the end (Phase 5). Real
slot-to-model mapping used lives in .claude/routing.local.md (gitignored).

## Updates to this file

Any change to AGENTS.md must:
1. Be approved by the senior chat
2. Maintain ASCII pure
3. Update SESSION_STATE.md with the decision
