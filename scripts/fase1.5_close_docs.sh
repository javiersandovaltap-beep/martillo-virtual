#!/usr/bin/env bash
# fase1.5_close_docs.sh - Cierra Fase 1.5: actualiza SESSION_STATE.md y ALTERNATIVES.md
# NO toca CLAUDE.md ni AGENTS.md (reservados para Fase 2)

echo "=== Fase 1.5: Cierre de documentacion de gobernanza ==="
echo ""

DIRTY=$(git status --porcelain --untracked-files=no)

if [ -n "$DIRTY" ]; then
    echo "AVISO: hay cambios sin commitear en archivos ya trackeados:"
    echo "$DIRTY"
    echo "Revisa antes de continuar. El script NO va a aplicar cambios."
else
    echo "[OK] working tree limpio, aplicando actualizaciones de docs"

    # --- 1. Actualizar Current state en SESSION_STATE.md ---
    sed -i 's/- Phase: v2.0 ROADMAP - Fase 1 (CI\/CD) CLOSED, Fase 1.5 (lint cleanup) next, then Fase 2/- Phase: v2.0 ROADMAP - Fase 1.5 (lint cleanup) CLOSED, Fase 2 (playbook enforcement) next/' SESSION_STATE.md
    sed -i 's/- Last commit: docs: close Fase 1 (CI\/CD with GitHub Actions)/- Last commit: ci: promote ruff lint job from informational to blocking/' SESSION_STATE.md
    sed -i 's/- Last tag: v2.0-fase1-stable/- Last tag: v2.0-fase1.5-stable/' SESSION_STATE.md
    sed -i 's/- Known flaky test: test_ratelimit.py::test_6th_attempt_blocked (see L30) -- passed clean in both CI runs so far, still deferred to Fase 3/- Known flaky test: test_ratelimit.py::test_6th_attempt_blocked (see L30) -- reproduced once more during Fase 1.5 isolated re-run (1 fail in full suite, 3\/3 pass standalone), still deferred to Fase 3/' SESSION_STATE.md
    sed -i 's/- Lint debt: 29 ruff findings (see D39 in ALTERNATIVES.md), tracked for Fase 1.5, NOT blocking CI yet/- Lint debt: RESOLVED (see D39 closure in ALTERNATIVES.md). Lint gate is now blocking in CI./' SESSION_STATE.md

    # --- 2. Insertar seccion de historial de Fase 1.5 despues de la de Fase 1 ---
    python3 - << 'PYEOF'
import re

with open("SESSION_STATE.md", "r", encoding="ascii") as f:
    content = f.read()

fase15_section = """
### Fase 1.5 - Lint cleanup (v2.0-fase1.5-stable)
- Root cause found before cleanup: venv (recreated during Fase 0 machine migration)
  never had requirements-dev.txt installed. Shell fell back to a global ruff 0.16.6
  install with an expanded default ruleset, producing 105 findings instead of the
  29 recorded at Fase 1 close. Fixed by installing requirements-dev.txt in the venv
  (see L32).
- Resolved 22/29 findings via `ruff check --fix .` (F401 unused imports across
  subastas/tests/*.py, views.py, management commands) -- commit 42c7835
- Resolved 3 F841 (unused local variables) via manual review:
  - test_backfill.py: 1 finding, required care because `s` is reused in the OTHER
    5 test methods in the same class -- a naive global sed would have broken them
    (see L33). Fixed via `sed` range-limited to the first occurrence only.
  - test_views.py: 2 findings (other_subasta, my_subasta), safe to remove --
    commit 718b4ea
- Resolved 2x F403 + 1x F405 in config/settings/ (intentional star imports,
  D01-D04) via explicit inline `# noqa: F403` / `# noqa: F405`, no refactor --
  commit 2113368
- Verified after each batch: pytest 125/125 passing, 98% coverage (no regression)
- Closed D39: lint job promoted from continue-on-error:true to blocking in
  .github/workflows/ci.yml -- commit 62fb82c, confirmed green in GitHub Actions
- `ruff check .` -> 0 findings (All checks passed!)
"""

marker = "## Phase history"
idx = content.find(marker)
insert_point = content.find("### Phase 0", idx)
content = content[:insert_point] + fase15_section.strip("\n") + "\n\n" + content[insert_point:]

with open("SESSION_STATE.md", "w", encoding="ascii") as f:
    f.write(content)
PYEOF

    # --- 3. Agregar lecciones L32 y L33 ---
    python3 - << 'PYEOF'
with open("SESSION_STATE.md", "r", encoding="ascii") as f:
    content = f.read()

marker = "L31: pytest-cov with --cov=<package>"
idx = content.find(marker)
end_of_l31 = content.find("\n\n", idx)

new_lessons = """

- L32: A venv recreated during a machine migration can silently omit dev-only dependencies (requirements-dev.txt) even when the base requirements.txt was installed correctly, because `pip install -r requirements.txt` alone gives no signal that a second dev file exists and was skipped. Symptom: a tool resolves via PATH to a DIFFERENT install (e.g. a global Python's Scripts folder) with a newer, unpinned version and an expanded default ruleset, producing results that look like new findings but are actually a version/config drift. Always verify `pip list` (or `pip show <package>`) inside the activated venv BEFORE trusting a tool's output, especially after any environment reproduction step (Fase 0 pattern).
- L33: When fixing ruff F841 (unused local variable) with a short, generic variable name (e.g. single-letter `s`) that repeats across multiple methods in the same test class, a naive find-and-replace (sed without occurrence limiting) can remove the assignment from methods where the variable IS used later, since ruff only flags the specific unused occurrence, not the name pattern. Always grep all occurrences of the exact variable name within the enclosing method/class scope before deciding removal vs prefix-with-underscore, and prefer occurrence-limited sed (e.g. `0,/pattern/{s/pattern/replacement/}`) over a global substitution when the same literal string appears in multiple, behaviorally different locations."""

content = content[:end_of_l31] + new_lessons + content[end_of_l31:]

with open("SESSION_STATE.md", "w", encoding="ascii") as f:
    f.write(content)
PYEOF

    # --- 4. Cerrar D39 en ALTERNATIVES.md ---
    python3 - << 'PYEOF'
with open("ALTERNATIVES.md", "r", encoding="ascii") as f:
    content = f.read()

old = """## D39: CI lint gate mode (informational vs blocking)

- Chosen: ruff check runs in CI as a separate job, non-blocking (continue-on-error: true)
- Alternative: blocking gate from the start (fail the workflow on any ruff finding)
- Reason: first-ever ruff run on ~67 commits of pre-existing code surfaced 29 findings
  (mostly F401 unused imports in tests, a few F841/F811, plus F403/F405 on intentional
  settings star-imports). Blocking immediately would have required mixing a large mechanical
  cleanup into the CI/CD setup thread (Fase 1), violating Phase discipline (CLAUDE.md rule 5).
- Action: cleanup deferred to Fase 1.5 (lint cleanup), a short dedicated thread before Fase 2.
  Once Fase 1.5 reaches 0 real findings, revisit continue-on-error and switch to blocking."""

new = """## D39: CI lint gate mode (informational vs blocking) -- CLOSED in Fase 1.5

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
  GitHub Actions. D39 is now closed -- no further action needed."""

content = content.replace(old, new)

with open("ALTERNATIVES.md", "w", encoding="ascii") as f:
    f.write(content)
PYEOF

    echo ""
    echo "=== Verificando ASCII pure (debe devolver 0 lineas) ==="
    grep -P "[^\x00-\x7F]" SESSION_STATE.md
    grep -P "[^\x00-\x7F]" ALTERNATIVES.md
    echo "(sin output arriba = ASCII pure OK)"

    echo ""
    echo "=== Diff generado ==="
    git diff SESSION_STATE.md ALTERNATIVES.md
fi

echo ""
echo "=== Script terminado. Si el diff se ve bien, corre: ==="
echo "  git add -A"
echo "  git commit -m \"docs: close Fase 1.5 (lint cleanup)\""
echo "  git tag -f v2.0-fase1.5-stable"
echo "  git push origin main --tags"
